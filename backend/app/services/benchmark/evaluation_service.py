"""
GBSkillEngine Benchmark 评测执行服务

负责执行评测运行并计算评测指标
"""
import time
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.benchmark import (
    BenchmarkDataset, BenchmarkCase, BenchmarkRun, BenchmarkResult,
    DatasetStatus, CaseDifficulty, RunStatus, ResultStatus
)
from app.schemas.benchmark import (
    EvaluationConfig, BenchmarkMetrics, OverallMetrics,
    DifficultyMetrics, AttributeMetrics, AttributeScore
)
from app.services.skill_runtime.runtime import SkillRuntime


class AttributeMatcher:
    """属性匹配器"""
    
    def __init__(self, config: EvaluationConfig):
        self.tolerance = config.tolerance
        self.partial_match = config.partial_match
    
    def match_attributes(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> Tuple[Dict[str, AttributeScore], float]:
        """
        匹配期望属性和实际属性
        
        Returns:
            (per_attribute_scores, overall_score)
        """
        scores: Dict[str, AttributeScore] = {}
        total_score = 0.0
        total_weight = 0
        
        # 遍历期望属性
        for attr_name, expected_attr in expected.items():
            expected_value = expected_attr.get("value") if isinstance(expected_attr, dict) else expected_attr
            expected_unit = expected_attr.get("unit", "") if isinstance(expected_attr, dict) else ""
            attr_tolerance = expected_attr.get("tolerance", self.tolerance) if isinstance(expected_attr, dict) else self.tolerance
            
            # 获取实际值
            actual_value = None
            if actual and attr_name in actual:
                actual_attr = actual[attr_name]
                if isinstance(actual_attr, dict):
                    actual_value = actual_attr.get("value")
                else:
                    actual_value = actual_attr
            
            # 计算匹配
            match_result = self._match_single_attribute(
                expected_value, actual_value, attr_tolerance
            )
            
            scores[attr_name] = AttributeScore(
                expected=expected_value,
                actual=actual_value,
                match=match_result["match"],
                score=match_result["score"],
                match_type=match_result["type"]
            )
            
            total_score += match_result["score"]
            total_weight += 1
        
        # 检查实际输出中的额外属性
        if actual:
            for attr_name in actual:
                if attr_name not in expected and not attr_name.startswith("_"):
                    # 额外属性不影响得分，但记录
                    actual_attr = actual[attr_name]
                    actual_value = actual_attr.get("value") if isinstance(actual_attr, dict) else actual_attr
                    scores[f"_extra_{attr_name}"] = AttributeScore(
                        expected=None,
                        actual=actual_value,
                        match=False,
                        score=0.0,
                        match_type="extra"
                    )
        
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        return scores, overall_score
    
    def _match_single_attribute(
        self,
        expected: Any,
        actual: Any,
        tolerance: Optional[float]
    ) -> Dict[str, Any]:
        """匹配单个属性值"""
        if actual is None:
            return {"match": False, "score": 0.0, "type": "missing"}
        
        # 精确匹配
        if expected == actual:
            return {"match": True, "score": 1.0, "type": "exact"}
        
        # 字符串归一化匹配
        if isinstance(expected, str) and isinstance(actual, str):
            if self._normalize_string(expected) == self._normalize_string(actual):
                return {"match": True, "score": 1.0, "type": "normalized"}
        
        # 数值容差匹配
        if tolerance and self._is_numeric(expected) and self._is_numeric(actual):
            exp_num = float(expected)
            act_num = float(actual)
            if exp_num == 0:
                if act_num == 0:
                    return {"match": True, "score": 1.0, "type": "exact"}
            else:
                diff_ratio = abs(exp_num - act_num) / abs(exp_num)
                if diff_ratio <= tolerance:
                    score = 1.0 - (diff_ratio / tolerance) * 0.5  # 容差内降分
                    return {"match": True, "score": score, "type": "tolerance"}
        
        # 模糊匹配 (部分匹配)
        if self.partial_match:
            fuzzy_score = self._fuzzy_match(expected, actual)
            if fuzzy_score > 0.5:
                return {"match": False, "score": fuzzy_score * 0.5, "type": "fuzzy"}
        
        return {"match": False, "score": 0.0, "type": "mismatch"}
    
    def _normalize_string(self, s: str) -> str:
        """字符串归一化"""
        return s.lower().strip().replace(" ", "").replace("-", "").replace("_", "")
    
    def _is_numeric(self, value: Any) -> bool:
        """检查是否为数值类型"""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False
    
    def _fuzzy_match(self, expected: Any, actual: Any) -> float:
        """模糊匹配得分"""
        str_exp = str(expected)
        str_act = str(actual)
        
        # 简单的字符重叠率
        if not str_exp or not str_act:
            return 0.0
        
        set_exp = set(str_exp)
        set_act = set(str_act)
        intersection = set_exp & set_act
        union = set_exp | set_act
        
        return len(intersection) / len(union) if union else 0.0


class BenchmarkEvaluationService:
    """评测执行服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_run(
        self,
        dataset_id: int,
        run_name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[EvaluationConfig] = None,
        created_by: Optional[str] = None
    ) -> BenchmarkRun:
        """创建评测运行"""
        # 检查数据集是否存在且就绪
        result = await self.db.execute(
            select(BenchmarkDataset).where(BenchmarkDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        if dataset.status == DatasetStatus.ARCHIVED:
            raise ValueError("Cannot run benchmark on archived dataset")
        
        # 统计用例数
        result = await self.db.execute(
            select(func.count(BenchmarkCase.id)).where(
                BenchmarkCase.dataset_id == dataset_id,
                BenchmarkCase.is_active == True
            )
        )
        total_cases = result.scalar() or 0
        
        if total_cases == 0:
            raise ValueError("Dataset has no active cases")
        
        # 创建运行记录
        run_code = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"
        
        run = BenchmarkRun(
            run_code=run_code,
            dataset_id=dataset_id,
            run_name=run_name or f"Benchmark Run {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=description,
            config=config.model_dump() if config else None,
            status=RunStatus.PENDING,
            total_cases=total_cases,
            completed_cases=0,
            created_by=created_by
        )
        
        self.db.add(run)
        await self.db.flush()
        
        return run
    
    async def execute_run(
        self,
        run_id: int,
        batch_size: int = 10
    ) -> BenchmarkRun:
        """执行评测运行"""
        # 加载运行记录
        result = await self.db.execute(
            select(BenchmarkRun).where(BenchmarkRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        if run.status == RunStatus.COMPLETED:
            return run
        
        if run.status == RunStatus.RUNNING:
            raise ValueError("Run is already in progress")
        
        # 更新状态为运行中
        run.status = RunStatus.RUNNING
        run.started_at = datetime.now()
        await self.db.flush()
        
        try:
            # 加载评测配置
            config = EvaluationConfig(**(run.config or {}))
            matcher = AttributeMatcher(config)
            
            # 加载所有待评测用例
            result = await self.db.execute(
                select(BenchmarkCase).where(
                    BenchmarkCase.dataset_id == run.dataset_id,
                    BenchmarkCase.is_active == True
                ).order_by(BenchmarkCase.id)
            )
            cases = result.scalars().all()
            
            # 初始化 Skill Runtime
            runtime = SkillRuntime(self.db)
            
            # 批量执行
            completed = 0
            for case in cases:
                try:
                    result_record = await self._evaluate_single_case(
                        case, run.id, runtime, matcher, config
                    )
                    completed += 1
                    
                    # 更新进度
                    if completed % batch_size == 0:
                        run.completed_cases = completed
                        await self.db.flush()
                        
                except Exception as e:
                    # 记录错误但继续执行
                    error_result = BenchmarkResult(
                        run_id=run.id,
                        case_id=case.id,
                        status=ResultStatus.ERROR,
                        error_message=str(e)
                    )
                    self.db.add(error_result)
                    completed += 1
            
            # 计算汇总指标
            metrics = await self._calculate_run_metrics(run.id)
            
            # 更新运行状态
            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.now()
            run.completed_cases = completed
            run.metrics = metrics.model_dump() if metrics else None
            
            await self.db.commit()
            return run
            
        except Exception as e:
            run.status = RunStatus.FAILED
            run.error_message = str(e)
            await self.db.commit()
            raise
    
    async def _evaluate_single_case(
        self,
        case: BenchmarkCase,
        run_id: int,
        runtime: SkillRuntime,
        matcher: AttributeMatcher,
        config: EvaluationConfig
    ) -> BenchmarkResult:
        """评测单个用例"""
        start_time = time.time()
        
        try:
            # 执行物料解析
            trace_id = f"bench_{run_id}_{case.id}"
            response = await runtime.execute(case.input_text, trace_id)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # 提取实际输出
            actual_skill_id = response.matched_skill_id
            actual_attributes = {}
            actual_category = None
            actual_confidence = None
            
            if response.result:
                # 转换属性格式
                for attr_name, attr_obj in response.result.attributes.items():
                    if hasattr(attr_obj, 'model_dump'):
                        actual_attributes[attr_name] = attr_obj.model_dump()
                    elif hasattr(attr_obj, '__dict__'):
                        actual_attributes[attr_name] = {
                            "value": getattr(attr_obj, 'value', None),
                            "unit": getattr(attr_obj, 'unit', ''),
                            "confidence": getattr(attr_obj, 'confidence', None)
                        }
                    else:
                        actual_attributes[attr_name] = {"value": attr_obj}
                
                actual_category = response.result.category
                actual_confidence = response.result.confidence
            
            # 计算 Skill 匹配
            skill_match = None
            if not config.skip_skill_match and case.expected_skill_id:
                skill_match = (actual_skill_id == case.expected_skill_id)
            
            # 计算属性匹配得分
            attribute_scores, overall_score = matcher.match_attributes(
                case.expected_attributes or {},
                actual_attributes
            )
            
            # 确定结果状态
            if skill_match is False:
                status = ResultStatus.FAILED
            elif overall_score >= 0.9:
                status = ResultStatus.SUCCESS
            elif overall_score >= 0.5:
                status = ResultStatus.PARTIAL
            else:
                status = ResultStatus.FAILED
            
            # 创建结果记录
            result = BenchmarkResult(
                run_id=run_id,
                case_id=case.id,
                actual_skill_id=actual_skill_id,
                actual_attributes=actual_attributes,
                actual_category=actual_category,
                actual_confidence=actual_confidence,
                execution_time_ms=execution_time_ms,
                skill_match=skill_match,
                attribute_scores={k: v.model_dump() for k, v in attribute_scores.items()},
                overall_score=overall_score,
                status=status
            )
            
            self.db.add(result)
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            result = BenchmarkResult(
                run_id=run_id,
                case_id=case.id,
                execution_time_ms=execution_time_ms,
                status=ResultStatus.ERROR,
                error_message=str(e)
            )
            
            self.db.add(result)
            return result
    
    async def _calculate_run_metrics(self, run_id: int) -> BenchmarkMetrics:
        """计算运行的汇总指标"""
        # 加载所有结果
        result = await self.db.execute(
            select(BenchmarkResult, BenchmarkCase).join(
                BenchmarkCase, BenchmarkResult.case_id == BenchmarkCase.id
            ).where(BenchmarkResult.run_id == run_id)
        )
        rows = result.all()
        
        if not rows:
            return BenchmarkMetrics(
                overall=OverallMetrics(
                    total_cases=0,
                    accuracy=0.0,
                    partial_accuracy=0.0,
                    skill_match_rate=0.0,
                    avg_confidence=0.0,
                    avg_score=0.0,
                    avg_execution_time_ms=0.0
                ),
                by_difficulty={},
                by_attribute={},
                by_status={}
            )
        
        # 汇总统计
        total = len(rows)
        success_count = 0
        partial_count = 0
        skill_match_count = 0
        skill_match_total = 0
        total_score = 0.0
        total_confidence = 0.0
        confidence_count = 0
        total_time_ms = 0
        
        by_difficulty: Dict[str, Dict] = {}
        by_attribute: Dict[str, Dict] = {}
        by_status: Dict[str, int] = {}
        
        for bench_result, case in rows:
            # 状态统计
            status_str = bench_result.status if bench_result.status else "unknown"
            by_status[status_str] = by_status.get(status_str, 0) + 1
            
            # 成功/部分成功统计
            if bench_result.status == ResultStatus.SUCCESS:
                success_count += 1
                partial_count += 1
            elif bench_result.status == ResultStatus.PARTIAL:
                partial_count += 1
            
            # Skill 匹配统计
            if bench_result.skill_match is not None:
                skill_match_total += 1
                if bench_result.skill_match:
                    skill_match_count += 1
            
            # 得分统计
            if bench_result.overall_score is not None:
                total_score += bench_result.overall_score
            
            # 置信度统计
            if bench_result.actual_confidence is not None:
                total_confidence += bench_result.actual_confidence
                confidence_count += 1
            
            # 时间统计
            if bench_result.execution_time_ms:
                total_time_ms += bench_result.execution_time_ms
            
            # 按难度统计
            difficulty = case.difficulty.value if case.difficulty else "unknown"
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = {
                    "count": 0,
                    "success": 0,
                    "total_score": 0.0
                }
            by_difficulty[difficulty]["count"] += 1
            if bench_result.status == ResultStatus.SUCCESS:
                by_difficulty[difficulty]["success"] += 1
            if bench_result.overall_score is not None:
                by_difficulty[difficulty]["total_score"] += bench_result.overall_score
            
            # 按属性统计
            if bench_result.attribute_scores:
                for attr_name, score_data in bench_result.attribute_scores.items():
                    if attr_name.startswith("_"):
                        continue
                    if attr_name not in by_attribute:
                        by_attribute[attr_name] = {
                            "total": 0,
                            "exact": 0,
                            "tolerance": 0,
                            "missing": 0
                        }
                    by_attribute[attr_name]["total"] += 1
                    match_type = score_data.get("match_type", "unknown")
                    if match_type == "exact" or match_type == "normalized":
                        by_attribute[attr_name]["exact"] += 1
                    elif match_type == "tolerance":
                        by_attribute[attr_name]["tolerance"] += 1
                    elif match_type == "missing":
                        by_attribute[attr_name]["missing"] += 1
        
        # 计算总体指标
        overall = OverallMetrics(
            total_cases=total,
            accuracy=success_count / total if total > 0 else 0.0,
            partial_accuracy=partial_count / total if total > 0 else 0.0,
            skill_match_rate=skill_match_count / skill_match_total if skill_match_total > 0 else 0.0,
            avg_confidence=total_confidence / confidence_count if confidence_count > 0 else 0.0,
            avg_score=total_score / total if total > 0 else 0.0,
            avg_execution_time_ms=total_time_ms / total if total > 0 else 0.0
        )
        
        # 转换难度指标
        difficulty_metrics = {}
        for diff, data in by_difficulty.items():
            count = data["count"]
            difficulty_metrics[diff] = DifficultyMetrics(
                count=count,
                accuracy=data["success"] / count if count > 0 else 0.0,
                avg_score=data["total_score"] / count if count > 0 else 0.0
            )
        
        # 转换属性指标
        attribute_metrics = {}
        for attr, data in by_attribute.items():
            total_attr = data["total"]
            attribute_metrics[attr] = AttributeMetrics(
                total=total_attr,
                exact_match=data["exact"] / total_attr if total_attr > 0 else 0.0,
                within_tolerance=(data["exact"] + data["tolerance"]) / total_attr if total_attr > 0 else 0.0,
                missing_rate=data["missing"] / total_attr if total_attr > 0 else 0.0
            )
        
        return BenchmarkMetrics(
            overall=overall,
            by_difficulty=difficulty_metrics,
            by_attribute=attribute_metrics,
            by_status=by_status
        )
    
    async def get_run_results(
        self,
        run_id: int,
        status_filter: Optional[List[ResultStatus]] = None,
        difficulty_filter: Optional[List[CaseDifficulty]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[BenchmarkResult], int]:
        """获取运行结果列表"""
        query = select(BenchmarkResult).where(BenchmarkResult.run_id == run_id)
        
        if status_filter:
            query = query.where(BenchmarkResult.status.in_(status_filter))
        
        if difficulty_filter:
            # 需要 join case 表
            query = query.join(BenchmarkCase).where(
                BenchmarkCase.difficulty.in_(difficulty_filter)
            )
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0
        
        # 分页查询
        query = query.order_by(BenchmarkResult.id).offset(offset).limit(limit)
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        return list(results), total
    
    async def get_failed_cases(self, run_id: int) -> List[Dict[str, Any]]:
        """获取失败的用例详情，用于分析"""
        result = await self.db.execute(
            select(BenchmarkResult, BenchmarkCase).join(
                BenchmarkCase, BenchmarkResult.case_id == BenchmarkCase.id
            ).where(
                BenchmarkResult.run_id == run_id,
                BenchmarkResult.status.in_([ResultStatus.FAILED, ResultStatus.ERROR])
            )
        )
        rows = result.all()
        
        failed_cases = []
        for bench_result, case in rows:
            failed_cases.append({
                "case_code": case.case_code,
                "input_text": case.input_text,
                "difficulty": case.difficulty.value if case.difficulty else None,
                "expected_skill_id": case.expected_skill_id,
                "expected_attributes": case.expected_attributes,
                "actual_skill_id": bench_result.actual_skill_id,
                "actual_attributes": bench_result.actual_attributes,
                "attribute_scores": bench_result.attribute_scores,
                "overall_score": bench_result.overall_score,
                "status": bench_result.status if bench_result.status else None,
                "error_message": bench_result.error_message,
                "source_reference": case.source_reference
            })
        
        return failed_cases
