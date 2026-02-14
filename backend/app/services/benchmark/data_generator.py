"""
GBSkillEngine Benchmark 数据生成服务

基于 Skill DSL 的多层数据生成策略:
- Layer 1: 种子数据 (真实标注)
- Layer 2: 表格枚举 (DSL表格的有效组合)
- Layer 3: 表达变体 (模板、同义词、噪声注入)
"""
import re
import random
import string
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from itertools import product
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill
from app.models.benchmark import (
    BenchmarkDataset, BenchmarkCase, GenerationTemplate,
    DatasetSourceType, DatasetStatus, CaseDifficulty, CaseSourceType
)
from app.schemas.benchmark import (
    BenchmarkCaseCreate, ExpectedAttribute, GenerationOptions, GenerationResult
)


class ValueDomainExtractor:
    """从 Skill DSL 提取属性值域"""
    
    def __init__(self, dsl_content: Dict[str, Any]):
        self.dsl = dsl_content
        self.tables = dsl_content.get("tables", {})
        self.attr_defs = dsl_content.get("attributeExtraction", {})
    
    def extract_all_domains(self) -> Dict[str, List[Any]]:
        """提取所有属性的值域"""
        domains = {}
        
        # 1. 从表格提取值域
        for table_name, table_data in self.tables.items():
            columns = table_data.get("columns", [])
            data = table_data.get("data", [])
            
            for col_idx, col_name in enumerate(columns):
                # 标准化列名
                attr_name = self._normalize_attr_name(col_name)
                if attr_name and data:
                    values = [row[col_idx] for row in data if len(row) > col_idx and row[col_idx] is not None]
                    if values:
                        if attr_name in domains:
                            domains[attr_name].extend(values)
                            domains[attr_name] = list(set(domains[attr_name]))
                        else:
                            domains[attr_name] = list(set(values))
        
        # 2. 从属性定义的枚举值提取
        for attr_name, attr_def in self.attr_defs.items():
            if "enum" in attr_def:
                domains[attr_name] = attr_def["enum"]
            elif "defaultValue" in attr_def and attr_name not in domains:
                domains[attr_name] = [attr_def["defaultValue"]]
        
        return domains
    
    def extract_table_combinations(self, table_name: str) -> List[Dict[str, Any]]:
        """提取单个表格的所有行作为属性组合"""
        if table_name not in self.tables:
            return []
        
        table = self.tables[table_name]
        columns = table.get("columns", [])
        data = table.get("data", [])
        
        combinations = []
        for row_idx, row in enumerate(data):
            combo = {
                "_source": {"table": table_name, "row_index": row_idx}
            }
            for col_idx, col_name in enumerate(columns):
                attr_name = self._normalize_attr_name(col_name)
                if attr_name and len(row) > col_idx:
                    combo[attr_name] = row[col_idx]
            combinations.append(combo)
        
        return combinations
    
    def get_cross_table_combinations(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """生成跨表的属性组合 (笛卡尔积，带限制)"""
        # 获取主要表格数据
        dn_table = self.tables.get("dn_outer_diameter_map", {})
        pn_table = self.tables.get("series_mapping", {})
        dim_table = self.tables.get("dimension_table", {})
        
        if not dn_table and not dim_table:
            return []
        
        combinations = []
        
        # 如果有尺寸表，直接使用其组合
        if dim_table:
            columns = dim_table.get("columns", [])
            data = dim_table.get("data", [])
            
            for row_idx, row in enumerate(data):
                # 基本组合
                base_combo = {}
                for col_idx, col_name in enumerate(columns):
                    if len(row) > col_idx:
                        attr_name = self._normalize_attr_name(col_name)
                        if attr_name:
                            base_combo[attr_name] = row[col_idx]
                
                # 对于包含多个壁厚列的表，为每个壁厚创建独立组合
                thickness_cols = [i for i, c in enumerate(columns) if "壁厚" in c or "厚" in c]
                if thickness_cols:
                    for thick_col in thickness_cols:
                        if len(row) > thick_col and row[thick_col]:
                            combo = base_combo.copy()
                            combo["壁厚"] = row[thick_col]
                            # 提取PN值
                            pn_match = re.search(r"PN?([\d.]+)", columns[thick_col])
                            if pn_match:
                                combo["公称压力"] = float(pn_match.group(1))
                            combo["_source"] = {
                                "table": "dimension_table",
                                "row_index": row_idx,
                                "col_index": thick_col
                            }
                            combinations.append(combo)
                else:
                    base_combo["_source"] = {"table": "dimension_table", "row_index": row_idx}
                    combinations.append(base_combo)
                
                if len(combinations) >= limit:
                    break
        
        return combinations[:limit]
    
    def _normalize_attr_name(self, col_name: str) -> Optional[str]:
        """标准化属性名称"""
        if not col_name:
            return None
        
        # 属性名映射
        mappings = {
            "DN": "公称直径",
            "dn": "公称直径",
            "外径": "公称外径",
            "外径(mm)": "公称外径",
            "PN": "公称压力",
            "pn": "公称压力",
            "壁厚": "壁厚",
            "长度": "长度",
            "规格": "规格",
        }
        
        # 直接匹配
        if col_name in mappings:
            return mappings[col_name]
        
        # 包含匹配
        for key, value in mappings.items():
            if key in col_name:
                return value
        
        # 清理单位后缀
        clean_name = re.sub(r'\([^)]*\)', '', col_name).strip()
        return clean_name if clean_name else None


class ExpressionTemplateEngine:
    """表达式模板引擎"""
    
    # 基础模板库
    DEFAULT_TEMPLATES = {
        "pipe": [
            # EASY: 标准格式
            "{材质}管 DN{公称直径} PN{公称压力}",
            "{材质}管材 DN{公称直径}mm PN{公称压力}MPa",
            "DN{公称直径} PN{公称压力} {材质}管",
            # MEDIUM: 部分信息缺失
            "{材质}管 DN{公称直径}",
            "DN{公称直径}管 {材质}",
            # HARD: 非标准写法
            "{材质}管道 直径{公称直径} 压力{公称压力}",
            "管材规格: DN{公称直径}, PN{公称压力}",
        ],
        "fastener": [
            # EASY
            "{头型}螺栓 {规格} {材质} {表面处理}",
            "{材质}{头型}螺栓{规格}",
            # MEDIUM
            "螺栓 {规格} {材质}",
            "{规格}螺栓",
            # HARD
            "{头型}螺丝 {规格}",
        ],
        "default": [
            "{name} {规格}",
            "{材质} {name}",
        ]
    }
    
    # 同义词替换表
    SYNONYMS = {
        "管": ["管材", "管道", "管子"],
        "螺栓": ["螺丝", "螺柱", "bolt"],
        "六角头": ["六角", "外六角", "Hex"],
        "PVC-U": ["UPVC", "PVC", "硬PVC", "聚氯乙烯"],
        "PPR": ["PP-R", "无规共聚聚丙烯"],
        "不锈钢": ["304不锈钢", "316不锈钢", "不锈钢材质"],
    }
    
    def __init__(self, domain: str = "default"):
        self.domain = domain
        self.templates = self.DEFAULT_TEMPLATES.get(domain, self.DEFAULT_TEMPLATES["default"])
    
    def generate_expression(self, attributes: Dict[str, Any], 
                            difficulty: CaseDifficulty = CaseDifficulty.EASY) -> str:
        """根据属性生成表达式"""
        # 选择合适难度的模板
        template = self._select_template(difficulty)
        
        # 渲染模板
        result = self._render_template(template, attributes)
        
        # 根据难度应用变换
        if difficulty == CaseDifficulty.MEDIUM:
            result = self._apply_medium_transforms(result)
        elif difficulty == CaseDifficulty.HARD:
            result = self._apply_hard_transforms(result, attributes)
        elif difficulty == CaseDifficulty.ADVERSARIAL:
            result = self._apply_adversarial_transforms(result, attributes)
        
        return result
    
    def _select_template(self, difficulty: CaseDifficulty) -> str:
        """根据难度选择模板"""
        if not self.templates:
            return "{name}"
        
        # 按难度分布选择模板
        if difficulty == CaseDifficulty.EASY:
            # 优先选择完整模板
            return self.templates[0]
        elif difficulty == CaseDifficulty.MEDIUM:
            # 选择中间模板
            idx = min(len(self.templates) // 2, len(self.templates) - 1)
            return self.templates[idx]
        else:
            # 选择最后的模板或随机
            return random.choice(self.templates)
    
    def _render_template(self, template: str, attributes: Dict[str, Any]) -> str:
        """渲染模板"""
        result = template
        for key, value in attributes.items():
            if key.startswith("_"):
                continue
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        # 清理未替换的占位符
        result = re.sub(r'\{[^}]+\}', '', result)
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    
    def _apply_medium_transforms(self, text: str) -> str:
        """应用中等难度变换"""
        transforms = [
            # 随机应用同义词替换
            lambda t: self._apply_synonym_replacement(t, prob=0.3),
            # 随机大小写变化
            lambda t: t.lower() if random.random() < 0.3 else t,
            # 单位省略
            lambda t: re.sub(r'(mm|MPa|cm|m)\b', '', t) if random.random() < 0.5 else t,
        ]
        
        result = text
        for transform in transforms:
            if random.random() < 0.5:
                result = transform(result)
        return result.strip()
    
    def _apply_hard_transforms(self, text: str, attributes: Dict[str, Any]) -> str:
        """应用困难级别变换"""
        # 先应用中等难度变换
        result = self._apply_medium_transforms(text)
        
        # 属性顺序打乱
        if random.random() < 0.3:
            words = result.split()
            random.shuffle(words)
            result = ' '.join(words)
        
        # 添加无关信息
        if random.random() < 0.3:
            noise_phrases = ["一批", "急需", "现货", "优质", "国标"]
            result = f"{random.choice(noise_phrases)} {result}"
        
        return result.strip()
    
    def _apply_adversarial_transforms(self, text: str, attributes: Dict[str, Any]) -> str:
        """应用对抗级别变换"""
        # 应用困难变换
        result = self._apply_hard_transforms(text, attributes)
        
        # 注入干扰
        if random.random() < 0.5:
            # 边界值处理
            result = self._inject_typos(result, prob=0.1)
        
        return result.strip()
    
    def _apply_synonym_replacement(self, text: str, prob: float = 0.3) -> str:
        """随机替换同义词"""
        result = text
        for word, synonyms in self.SYNONYMS.items():
            if word in result and random.random() < prob:
                result = result.replace(word, random.choice(synonyms), 1)
        return result
    
    def _inject_typos(self, text: str, prob: float = 0.1) -> str:
        """注入错别字/拼写错误"""
        if random.random() > prob:
            return text
        
        typo_map = {
            "管材": "管才",
            "螺栓": "螺拴",
            "直径": "直经",
            "压力": "压励",
        }
        
        for correct, typo in typo_map.items():
            if correct in text and random.random() < prob:
                text = text.replace(correct, typo, 1)
                break
        
        return text


class NoiseInjector:
    """噪声注入器"""
    
    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        self.rules = rules or {}
    
    def inject(self, text: str, difficulty: CaseDifficulty) -> str:
        """根据难度注入噪声"""
        noise_level = {
            CaseDifficulty.EASY: 0.0,
            CaseDifficulty.MEDIUM: 0.2,
            CaseDifficulty.HARD: 0.4,
            CaseDifficulty.ADVERSARIAL: 0.6,
        }.get(difficulty, 0.0)
        
        if random.random() > noise_level:
            return text
        
        noise_functions = [
            self._add_prefix_noise,
            self._add_suffix_noise,
            self._swap_characters,
            self._add_spaces,
        ]
        
        # 随机选择一种噪声注入方式
        noise_func = random.choice(noise_functions)
        return noise_func(text)
    
    def _add_prefix_noise(self, text: str) -> str:
        """添加前缀噪声"""
        prefixes = ["采购", "询价", "需要", "订购", "紧急采购"]
        return f"{random.choice(prefixes)} {text}"
    
    def _add_suffix_noise(self, text: str) -> str:
        """添加后缀噪声"""
        suffixes = ["若干", "100根", "一批", "1000个", "等"]
        return f"{text} {random.choice(suffixes)}"
    
    def _swap_characters(self, text: str) -> str:
        """交换相邻字符"""
        if len(text) < 4:
            return text
        chars = list(text)
        idx = random.randint(1, len(chars) - 2)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return ''.join(chars)
    
    def _add_spaces(self, text: str) -> str:
        """添加额外空格"""
        words = text.split()
        if len(words) > 1:
            idx = random.randint(0, len(words) - 1)
            words[idx] = words[idx] + "  "
        return ' '.join(words)


class BenchmarkDataGenerator:
    """评测数据生成服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_from_skill(
        self,
        skill_id: int,
        options: GenerationOptions,
        dataset_id: int
    ) -> GenerationResult:
        """从 Skill DSL 生成测试数据"""
        # 1. 加载 Skill
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        dsl = skill.dsl_content
        domain = dsl.get("domain", "default")
        
        # 2. 提取值域
        extractor = ValueDomainExtractor(dsl)
        combinations = extractor.get_cross_table_combinations(limit=options.count * 2)
        
        if not combinations:
            # 如果没有表格数据，使用值域笛卡尔积
            domains = extractor.extract_all_domains()
            combinations = self._generate_combinations_from_domains(domains, options.count * 2)
        
        # 3. 初始化生成器
        template_engine = ExpressionTemplateEngine(domain)
        noise_injector = NoiseInjector()
        
        # 4. 计算难度分布
        difficulty_dist = self._calculate_difficulty_distribution(
            options.difficulty_distribution,
            options.count
        )
        
        # 5. 生成用例
        generated_cases: List[BenchmarkCase] = []
        stats = {
            "by_difficulty": {d.value: 0 for d in CaseDifficulty},
            "by_source": {s.value: 0 for s in CaseSourceType},
            "total_combinations": len(combinations),
        }
        
        combo_idx = 0
        for difficulty, count in difficulty_dist.items():
            for _ in range(count):
                if combo_idx >= len(combinations):
                    combo_idx = 0  # 循环使用组合
                
                combo = combinations[combo_idx]
                combo_idx += 1
                
                # 添加默认属性
                attrs_for_gen = combo.copy()
                if "材质" not in attrs_for_gen:
                    # 从 DSL 获取默认材质
                    default_material = dsl.get("attributeExtraction", {}).get("材质", {}).get("defaultValue")
                    if default_material:
                        attrs_for_gen["材质"] = default_material
                
                # 生成表达式
                input_text = template_engine.generate_expression(attrs_for_gen, difficulty)
                
                # 注入噪声
                if options.include_noise:
                    input_text = noise_injector.inject(input_text, difficulty)
                
                # 构建期望属性
                expected_attrs = {}
                for attr_name, attr_value in combo.items():
                    if attr_name.startswith("_"):
                        continue
                    unit = self._get_attr_unit(attr_name, dsl)
                    expected_attrs[attr_name] = {
                        "value": attr_value,
                        "unit": unit,
                        "tolerance": self._get_tolerance(attr_name)
                    }
                
                # 创建用例
                case_code = f"GEN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
                
                case = BenchmarkCase(
                    dataset_id=dataset_id,
                    case_code=case_code,
                    input_text=input_text,
                    expected_skill_id=skill.skill_id,
                    expected_attributes=expected_attrs,
                    expected_category=dsl.get("categoryMapping"),
                    difficulty=difficulty,
                    source_type=CaseSourceType.TABLE_ENUM,
                    source_reference=combo.get("_source", {}),
                    is_active=True
                )
                
                self.db.add(case)
                generated_cases.append(case)
                
                # 更新统计
                stats["by_difficulty"][difficulty.value] += 1
                stats["by_source"][CaseSourceType.TABLE_ENUM.value] += 1
                
                if len(generated_cases) >= options.count:
                    break
            
            if len(generated_cases) >= options.count:
                break
        
        # 6. 提交到数据库
        await self.db.flush()
        
        # 7. 更新数据集统计
        await self._update_dataset_stats(dataset_id, stats["by_difficulty"])
        
        return GenerationResult(
            generated_count=len(generated_cases),
            cases=[],  # 简化返回，避免序列化问题
            stats=stats
        )
    
    async def generate_from_template(
        self,
        template_id: int,
        attributes: Dict[str, List[Any]],
        count: int,
        dataset_id: int,
        difficulty: CaseDifficulty = CaseDifficulty.MEDIUM
    ) -> GenerationResult:
        """从模板生成测试数据"""
        # 加载模板
        result = await self.db.execute(
            select(GenerationTemplate).where(GenerationTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        generated_cases: List[BenchmarkCase] = []
        noise_injector = NoiseInjector(template.noise_rules)
        
        # 生成属性组合
        combinations = self._generate_combinations_from_domains(attributes, count)
        
        for combo in combinations[:count]:
            # 渲染模板
            input_text = template.pattern
            for key, value in combo.items():
                input_text = input_text.replace(f"{{{key}}}", str(value))
            
            # 应用变体
            if template.variants and random.random() < 0.3:
                variant = random.choice(template.variants)
                for key, value in combo.items():
                    variant = variant.replace(f"{{{key}}}", str(value))
                input_text = variant
            
            # 注入噪声
            input_text = noise_injector.inject(input_text, difficulty)
            
            # 构建期望属性
            expected_attrs = {
                k: {"value": v, "unit": "", "tolerance": None}
                for k, v in combo.items()
            }
            
            case_code = f"TPL_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
            
            case = BenchmarkCase(
                dataset_id=dataset_id,
                case_code=case_code,
                input_text=input_text,
                expected_attributes=expected_attrs,
                difficulty=difficulty,
                source_type=CaseSourceType.TEMPLATE,
                source_reference={"template_id": template_id},
                is_active=True
            )
            
            self.db.add(case)
            generated_cases.append(case)
        
        await self.db.flush()
        
        stats = {
            "by_difficulty": {difficulty.value: len(generated_cases)},
            "by_source": {CaseSourceType.TEMPLATE.value: len(generated_cases)},
        }
        
        await self._update_dataset_stats(dataset_id, stats["by_difficulty"])
        
        return GenerationResult(
            generated_count=len(generated_cases),
            cases=[],
            stats=stats
        )
    
    def _generate_combinations_from_domains(
        self,
        domains: Dict[str, List[Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """从值域生成组合"""
        if not domains:
            return []
        
        keys = list(domains.keys())
        values = [domains[k] for k in keys]
        
        # 笛卡尔积
        all_combos = list(product(*values))
        
        # 随机采样
        if len(all_combos) > limit:
            all_combos = random.sample(all_combos, limit)
        
        return [
            dict(zip(keys, combo))
            for combo in all_combos
        ]
    
    def _calculate_difficulty_distribution(
        self,
        custom_dist: Optional[Dict[str, int]],
        total: int
    ) -> Dict[CaseDifficulty, int]:
        """计算难度分布"""
        if custom_dist:
            # 按百分比分配
            result = {}
            remaining = total
            for diff_str, pct in custom_dist.items():
                try:
                    diff = CaseDifficulty(diff_str)
                    count = int(total * pct / 100)
                    result[diff] = count
                    remaining -= count
                except ValueError:
                    continue
            
            # 分配剩余
            if remaining > 0 and result:
                first_key = list(result.keys())[0]
                result[first_key] += remaining
            
            return result
        
        # 默认分布: 40% easy, 30% medium, 20% hard, 10% adversarial
        return {
            CaseDifficulty.EASY: int(total * 0.4),
            CaseDifficulty.MEDIUM: int(total * 0.3),
            CaseDifficulty.HARD: int(total * 0.2),
            CaseDifficulty.ADVERSARIAL: total - int(total * 0.4) - int(total * 0.3) - int(total * 0.2),
        }
    
    def _get_attr_unit(self, attr_name: str, dsl: Dict[str, Any]) -> str:
        """获取属性单位"""
        attr_defs = dsl.get("attributeExtraction", {})
        if attr_name in attr_defs:
            return attr_defs[attr_name].get("unit", "")
        
        # 常见单位映射
        unit_map = {
            "公称直径": "mm",
            "公称外径": "mm",
            "公称压力": "MPa",
            "壁厚": "mm",
            "长度": "mm",
        }
        return unit_map.get(attr_name, "")
    
    def _get_tolerance(self, attr_name: str) -> Optional[float]:
        """获取属性容差"""
        # 数值类属性设置默认容差
        numeric_attrs = {"公称直径", "公称外径", "壁厚", "长度", "公称压力"}
        if attr_name in numeric_attrs:
            return 0.05  # 5% 容差
        return None
    
    async def _update_dataset_stats(
        self,
        dataset_id: int,
        difficulty_counts: Dict[str, int]
    ):
        """更新数据集统计信息"""
        result = await self.db.execute(
            select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()
        if dataset:
            # 合并难度分布
            current_dist = dataset.difficulty_distribution or {}
            for diff, count in difficulty_counts.items():
                current_dist[diff] = current_dist.get(diff, 0) + count
            dataset.difficulty_distribution = current_dist
            
            # 更新总数
            dataset.total_cases = sum(current_dist.values())
            
            await self.db.flush()
