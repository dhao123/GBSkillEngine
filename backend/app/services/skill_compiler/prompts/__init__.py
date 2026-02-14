"""
GBSkillEngine Skill编译Prompt模板
"""

# 系统角色设定
SYSTEM_PROMPT = """你是一位MRO工业品领域的国标分析专家，精通各类国家标准的解读和结构化处理。
你的任务是根据国标文档信息，生成用于物料解析的Skill DSL配置。

输出要求：
1. 必须输出有效的JSON格式
2. 不要包含任何额外的解释文字
3. 严格遵循指定的JSON结构
4. 属性提取的正则表达式要准确可用
5. 充分利用文档内容，提取准确的技术参数"""


# 领域检测Prompt
DOMAIN_DETECTION_PROMPT = """分析以下国标信息，判断其所属的工业领域。

国标编号: {standard_code}
国标名称: {standard_name}
产品范围: {product_scope}

请从以下领域中选择最匹配的一个：
- pipe: 管材管道类（包括PVC管、PE管、PPR管、钢管等）
- fastener: 紧固件类（包括螺栓、螺钉、螺母、垫片等）
- valve: 阀门类（包括闸阀、球阀、蝶阀等）
- fitting: 管件类（包括弯头、三通、法兰等）
- cable: 电缆电线类
- bearing: 轴承类
- seal: 密封件类
- general: 通用/其他

请只输出JSON格式：
{{"domain": "领域代码", "confidence": 置信度0-1, "reason": "判断理由"}}"""


# 属性抽取Prompt（增强版）
ATTRIBUTE_EXTRACTION_PROMPT = """根据以下国标信息和文档内容，提取该类物料的完整属性定义。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}

文档内容:
{document_content}

请仔细分析文档内容，提取所有关键属性。每个属性需要包含：
- type: 属性类型 (dimension/material/performance/specification/category)
- unit: 单位（如mm、MPa等，无单位可省略）
- patterns: 用于从物料描述中提取该属性值的正则表达式列表（至少提供2个变体）
- required: 是否为必填属性
- defaultValue: 默认值（如适用）
- allowedValues: 允许的值列表（如适用）
- displayName: 显示名称（用于输出展示）
- description: 属性说明（包含标准依据）

对于管材类(pipe)，必须包含以下属性：
1. 公称直径(DN) - 从DN或dn开头的规格中提取
2. 公称压力(PN) - 从PN或pn开头的规格中提取
3. 材质 - 如UPVC、PVC-U、PE、PPR等
4. 公称外径 - 可从DN查表获得
5. 管系列(S) - 可从PN查表获得
6. 最小壁厚 - 可从外径和管系列查表获得

输出JSON格式示例：
{{
  "公称直径": {{
    "type": "dimension",
    "unit": "mm",
    "patterns": ["DN(\\\\d+)", "dn(\\\\d+)", "公称直径[：:]?(\\\\d+)"],
    "required": true,
    "displayName": "公称直径(DN)",
    "description": "用户输入规格"
  }},
  "公称压力": {{
    "type": "dimension",
    "unit": "MPa",
    "patterns": ["PN([\\\\d.]+)", "pn([\\\\d.]+)", "公称压力[：:]?([\\\\d.]+)"],
    "required": false,
    "displayName": "公称压力(PN)",
    "description": "用户输入，对应标准中的PN系列"
  }},
  "材质": {{
    "type": "material",
    "patterns": ["(UPVC|PVC-U|PVC|PE100|PE80|PPR|PP-R|硬聚氯乙烯)"],
    "required": false,
    "defaultValue": "PVC-U",
    "displayName": "管件材质",
    "description": "以聚氯乙烯(PVC)树脂为主要原料的混配料"
  }}
}}

请根据文档内容提取完整的属性定义："""


# 意图识别Prompt
INTENT_RECOGNITION_PROMPT = """根据以下国标信息，生成用于识别该类物料的关键词和正则模式。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}
已提取属性: {attributes}

请生成：
1. keywords: 用于快速匹配的关键词列表（中英文），需要包含：
   - 产品类型关键词（如：管、管材、管道）
   - 材质关键词（如：UPVC、PVC、PE）
   - 规格前缀（如：DN、PN、M）
   - 行业术语

2. patterns: 用于精确匹配的正则表达式列表，需要覆盖：
   - 规格格式（如DN100、PN1.6、M10×50）
   - 材质标识
   - 组合格式（如UPVC管DN100PN1.6）

输出JSON格式：
{{
  "keywords": ["关键词1", "关键词2", ...],
  "patterns": ["正则表达式1", "正则表达式2", ...]
}}

示例：
管材类: 
{{
  "keywords": ["管", "管材", "管道", "给水管", "排水管", "DN", "PN", "UPVC", "PVC-U", "PVC", "PE", "PPR", "硬聚氯乙烯"],
  "patterns": ["(DN|dn)\\\\d+", "(PN|pn)[\\\\d.]+", "UPVC|PVC-U|PVC|PE\\\\d*|PPR|PP-R", "(UPVC|PVC|PE|PPR).*(DN|dn)\\\\d+"]
}}"""


# 类目映射Prompt（增强版）
CATEGORY_MAPPING_PROMPT = """根据以下国标信息，生成物料的类目映射规则。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}

请生成四级类目结构：
- primaryCategory: 一级类目（如：管道系统）
- secondaryCategory: 二级类目（如：工业用塑料管道）
- tertiaryCategory: 三级类目（如：硬聚氯乙烯(PVC-U)）
- quaternaryCategory: 四级类目（如：工业用PVC-U管材）
- categoryId: 类目ID（格式：CAT_XXX_001）
- commonName: 通用名称（标准规定的产品名称）

输出JSON格式：
{{
  "primaryCategory": "一级类目",
  "secondaryCategory": "二级类目", 
  "tertiaryCategory": "三级类目",
  "quaternaryCategory": "四级类目",
  "categoryId": "CAT_XXX_001",
  "commonName": "通用名称"
}}

示例（GB/T 4219.1 工业用PVC-U管道系统）:
{{
  "primaryCategory": "管道系统",
  "secondaryCategory": "工业用塑料管道",
  "tertiaryCategory": "硬聚氯乙烯(PVC-U)",
  "quaternaryCategory": "工业用PVC-U管材",
  "categoryId": "CAT_PIPE_PVCU_001",
  "commonName": "工业用硬聚氯乙烯(PVC-U)管材"
}}"""


# 表格数据提取Prompt（增强版）
TABLE_EXTRACTION_PROMPT = """根据以下国标文档内容，提取其中的尺寸规格表和参数对照表。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}

文档内容:
{document_content}

重要提取要求：
1. 如果文档内容中包含表格数据（以"|"分隔或对齐排列的数字），请直接提取原始数据，不要编造
2. 数值类数据使用number类型（如 110、3.4），文字类数据使用string类型（如 "S20"、"M6"）
3. 注意"±"符号表示公差范围，保留原始精度
4. 如果表格跨页或被截断，提取已有部分并在description中标注"数据可能不完整"
5. 如果文档中确实没有表格数据，根据该国标的通用知识填充典型值，并在source中标注"基于国标通用知识"

请从文档中提取以下类型的表格数据：

对于管材类(pipe)：
1. dn_outer_diameter_map: 公称直径(DN)到公称外径(mm)的映射表
2. series_mapping: 公称压力(PN)到管系列(S)的映射表
3. dimension_table: 外径与壁厚对应表（按管系列S分列）
4. wall_thickness_tolerance: 壁厚偏差表

对于紧固件类(fastener)：
1. thread_spec_table: 螺纹规格表
2. strength_grade_table: 强度等级表

输出JSON格式：
{{
  "dn_outer_diameter_map": {{
    "description": "表格描述",
    "source": "来源（如GB/T 4219.1 表2）",
    "columns": ["列名1", "列名2"],
    "data": [[值1, 值2], [值3, 值4], ...]
  }},
  "series_mapping": {{
    "description": "PN等级到管系列S的映射",
    "source": "来源",
    "columns": ["PN", "管系列S", "设计系数C"],
    "data": [[0.6, "S20", 2.0], [1.6, "S8", 2.0], ...]
  }},
  "dimension_table": {{
    "description": "管材尺寸表",
    "source": "来源",
    "columns": ["公称外径(mm)", "S20壁厚", "S16壁厚", "S12.5壁厚", "S10壁厚", "S8壁厚", "S6.3壁厚", "S5壁厚"],
    "data": [[110, 2.7, 3.4, 4.2, 5.3, 6.6, 8.2, 10.0], ...]
  }},
  "wall_thickness_tolerance": {{
    "description": "壁厚偏差表",
    "source": "来源",
    "columns": ["壁厚范围(mm)", "壁厚偏差(mm)"],
    "data": [["6.1-10.0", 0.9], ...]
  }}
}}

请尽量从文档中提取准确数据："""


# Vision表格提取Prompt（新增 - 用于多模态视觉API）
VISION_TABLE_EXTRACTION_PROMPT = """你是一位MRO工业品国标分析专家。请仔细查看以下国标文档页面图片，提取其中所有表格数据。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}

提取要求：
1. 识别每个表格的标题（如"表1 管材尺寸"、"表2 DN与公称外径对照"）
2. 提取完整的表头（column headers）和每一行数据
3. 正确处理合并单元格（上方或左方的值延续到合并区域）
4. 注意特殊符号："±"表示公差范围，"-"在数据中通常表示"无此规格"或"不适用"
5. 数值保持原始精度，不要四舍五入
6. 如果表格被截断（跨页），提取可见部分并在description中标注

输出JSON格式，按表格类型归类：
{{
  "dn_outer_diameter_map": {{
    "description": "表格描述",
    "source": "图片中看到的表格标题/编号",
    "columns": ["列名1", "列名2"],
    "data": [[值1, 值2], ...]
  }},
  "dimension_table": {{
    "description": "管材尺寸表",
    "source": "图片中看到的表格标题/编号",
    "columns": ["列名1", "列名2", ...],
    "data": [[值1, 值2, ...], ...]
  }}
}}

如果看到的表格不属于以上预定义类型，使用描述性key名（如"chemical_composition_table"）。
请仔细分析图片中的每个表格："""


# 完整DSL生成Prompt
FULL_DSL_GENERATION_PROMPT = """根据以下国标信息，生成完整的Skill DSL配置。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}
文档摘要: {document_summary}

请生成完整的Skill DSL，包含以下字段：
1. skillId: 格式为 skill_{{standard_code的下划线形式}}
2. skillName: {{standard_name}} Skill
3. version: "1.0.0"
4. domain: {domain}
5. applicableMaterialTypes: 适用的物料类型列表
6. priority: 优先级（默认100）
7. intentRecognition: 意图识别规则（keywords和patterns）
8. attributeExtraction: 属性抽取规则
9. tables: 相关数据表（如尺寸规格表）
10. categoryMapping: 类目映射
11. outputStructure: 输出模板
12. fallbackStrategy: 回退策略

输出完整的JSON格式DSL配置："""


# DSL JSON Schema
DSL_JSON_SCHEMA = {
    "type": "object",
    "required": ["skillId", "skillName", "version", "domain", "attributeExtraction"],
    "properties": {
        "skillId": {"type": "string"},
        "skillName": {"type": "string"},
        "version": {"type": "string"},
        "domain": {"type": "string"},
        "standardCode": {"type": "string"},
        "applicableMaterialTypes": {
            "type": "array",
            "items": {"type": "string"}
        },
        "priority": {"type": "integer"},
        "intentRecognition": {
            "type": "object",
            "properties": {
                "keywords": {"type": "array", "items": {"type": "string"}},
                "patterns": {"type": "array", "items": {"type": "string"}}
            }
        },
        "attributeExtraction": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "unit": {"type": "string"},
                    "patterns": {"type": "array", "items": {"type": "string"}},
                    "required": {"type": "boolean"},
                    "defaultValue": {"type": "string"},
                    "allowedValues": {"type": "array", "items": {"type": "string"}},
                    "displayName": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        },
        "tables": {"type": "object"},
        "categoryMapping": {
            "type": "object",
            "properties": {
                "primaryCategory": {"type": "string"},
                "secondaryCategory": {"type": "string"},
                "tertiaryCategory": {"type": "string"},
                "quaternaryCategory": {"type": "string"},
                "categoryId": {"type": "string"},
                "commonName": {"type": "string"}
            }
        },
        "outputStructure": {"type": "object"},
        "fallbackStrategy": {
            "type": "object",
            "properties": {
                "lowConfidenceThreshold": {"type": "number"},
                "humanReviewRequired": {"type": "boolean"}
            }
        }
    }
}
