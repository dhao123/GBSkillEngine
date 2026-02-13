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
4. 属性提取的正则表达式要准确可用"""


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


# 属性抽取Prompt
ATTRIBUTE_EXTRACTION_PROMPT = """根据以下国标信息，提取该类物料的属性定义。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}
文档摘要: {document_summary}

请分析该国标涉及的物料，提取其关键属性。每个属性需要：
- type: 属性类型 (dimension/material/performance/specification)
- unit: 单位（如适用）
- patterns: 用于从物料描述中提取该属性值的正则表达式列表
- required: 是否为必填属性
- defaultValue: 默认值（如适用）
- allowedValues: 允许的值列表（如适用）

输出JSON格式：
{{
  "属性中文名": {{
    "type": "属性类型",
    "unit": "单位",
    "patterns": ["正则表达式1", "正则表达式2"],
    "required": true/false,
    "defaultValue": "默认值",
    "allowedValues": ["值1", "值2"]
  }}
}}

示例：
对于管材类国标，可能提取的属性包括：
- 公称直径: type=dimension, unit=mm, patterns=["DN(\\d+)", "直径(\\d+)"]
- 公称压力: type=dimension, unit=MPa, patterns=["PN([\\d.]+)"]
- 材质: type=material, patterns=["(UPVC|PVC|PE|PPR)"]

请根据国标内容提取属性定义："""


# 意图识别Prompt
INTENT_RECOGNITION_PROMPT = """根据以下国标信息，生成用于识别该类物料的关键词和正则模式。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}
已提取属性: {attributes}

请生成：
1. keywords: 用于快速匹配的关键词列表（中英文）
2. patterns: 用于精确匹配的正则表达式列表

输出JSON格式：
{{
  "keywords": ["关键词1", "关键词2", ...],
  "patterns": ["正则表达式1", "正则表达式2", ...]
}}

示例：
管材类: keywords=["管", "管材", "管道", "DN", "PN", "UPVC"], patterns=["(DN|dn)\\d+", "UPVC|PVC|PE"]
紧固件类: keywords=["螺栓", "螺钉", "螺母", "M6", "M8"], patterns=["M\\d+[×x]\\d+"]"""


# 类目映射Prompt
CATEGORY_MAPPING_PROMPT = """根据以下国标信息，生成物料的类目映射规则。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}

请生成三级类目结构：
- primaryCategory: 一级类目（如：管材、紧固件、阀门）
- secondaryCategory: 二级类目（如：塑料管、金属螺栓）
- tertiaryCategory: 三级类目（如：PVC-U管、六角头螺栓）
- categoryId: 类目ID（格式：CAT_XXX_001）

输出JSON格式：
{{
  "primaryCategory": "一级类目",
  "secondaryCategory": "二级类目", 
  "tertiaryCategory": "三级类目",
  "categoryId": "CAT_XXX_001"
}}"""


# 完整DSL生成Prompt
FULL_DSL_GENERATION_PROMPT = """根据以下国标信息，生成完整的Skill DSL配置。

国标编号: {standard_code}
国标名称: {standard_name}
领域: {domain}
产品范围: {product_scope}
文档摘要: {document_summary}

请生成完整的Skill DSL，包含以下字段：
1. skillId: 格式为 skill_{standard_code的下划线形式}
2. skillName: {standard_name} Skill
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
                    "allowedValues": {"type": "array", "items": {"type": "string"}}
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
                "categoryId": {"type": "string"}
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
