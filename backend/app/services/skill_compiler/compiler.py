"""
GBSkillEngine Skill编译器 (Mock模式)

将国标文档编译为Skill DSL
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.standard import Standard
from app.models.skill import Skill, SkillStatus


# 预定义的Skill DSL模板
SKILL_TEMPLATES = {
    "pipe": {
        "skillId": "skill_pipe_template",
        "skillName": "管材Skill模板",
        "version": "1.0.0",
        "domain": "pipe",
        "applicableMaterialTypes": ["管材", "管道", "塑料管", "UPVC管", "PVC管", "PE管"],
        "priority": 100,
        "intentRecognition": {
            "keywords": ["管", "管材", "管道", "DN", "PN", "UPVC", "PVC", "PE", "PPR"],
            "patterns": ["(DN|dn)\\d+", "(PN|pn)[\\d.]+", "UPVC|PVC|PE|PPR"]
        },
        "attributeExtraction": {
            "公称直径": {
                "type": "dimension",
                "unit": "mm",
                "patterns": ["DN(\\d+)", "dn(\\d+)", "直径(\\d+)"],
                "required": True
            },
            "公称压力": {
                "type": "dimension",
                "unit": "MPa",
                "patterns": ["PN([\\d.]+)", "pn([\\d.]+)", "压力([\\d.]+)"],
                "required": False
            },
            "材质": {
                "type": "material",
                "patterns": ["(UPVC|PVC-U|PVC|PE|PPR|PP-R)"],
                "defaultValue": "PVC-U",
                "required": False
            },
            "管系列": {
                "type": "dimension",
                "patterns": ["S(\\d+)", "系列(\\d+)"],
                "required": False
            }
        },
        "rules": {
            "dnToOuterDiameter": {
                "type": "mapping",
                "description": "DN到外径的映射",
                "mappingTable": "dn_outer_diameter_map"
            },
            "pnToWallThickness": {
                "type": "mapping",
                "description": "压力等级到壁厚的映射",
                "mappingTable": "pn_wall_thickness_map"
            }
        },
        "tables": {
            "dn_outer_diameter_map": {
                "description": "公称直径与外径映射表",
                "columns": ["DN", "外径(mm)"],
                "data": [
                    [20, 25], [25, 32], [32, 40], [40, 50], [50, 63],
                    [65, 75], [80, 90], [100, 110], [125, 140], [150, 160],
                    [200, 225], [250, 280], [300, 315], [400, 450], [500, 560]
                ]
            },
            "dimension_table": {
                "description": "尺寸规格表 (GB/T 4219.1)",
                "columns": ["DN", "外径", "PN0.6壁厚", "PN1.0壁厚", "PN1.6壁厚"],
                "data": [
                    [50, 63, 1.9, 2.0, 3.0],
                    [65, 75, 2.3, 2.9, 3.6],
                    [80, 90, 2.8, 3.5, 4.3],
                    [100, 110, 3.4, 4.2, 5.3],
                    [125, 140, 4.3, 5.4, 6.7],
                    [150, 160, 4.9, 6.2, 7.7],
                    [200, 225, 6.9, 8.6, 10.8],
                    [250, 280, 8.6, 10.7, 13.4],
                    [300, 315, 9.7, 12.1, 15.0]
                ]
            }
        },
        "categoryMapping": {
            "primaryCategory": "管材",
            "secondaryCategory": "塑料管",
            "tertiaryCategory": "PVC-U管",
            "categoryId": "CAT_PIPE_001"
        },
        "outputStructure": {
            "物料名称": "{材质}管 {公称直径}",
            "类目": "{primaryCategory}/{secondaryCategory}/{tertiaryCategory}",
            "规格参数": {
                "公称直径DN": "{公称直径}",
                "公称外径": "{外径}",
                "公称压力PN": "{公称压力}",
                "管系列S": "{管系列}",
                "最小壁厚": "{壁厚}",
                "材质": "{材质}"
            },
            "适用标准": "{standardCode}"
        },
        "fallbackStrategy": {
            "lowConfidenceThreshold": 0.6,
            "humanReviewRequired": True
        }
    },
    "fastener": {
        "skillId": "skill_fastener_template",
        "skillName": "紧固件Skill模板",
        "version": "1.0.0",
        "domain": "fastener",
        "applicableMaterialTypes": ["螺栓", "螺钉", "螺母", "紧固件"],
        "priority": 100,
        "intentRecognition": {
            "keywords": ["螺栓", "螺钉", "螺母", "垫片", "M6", "M8", "M10", "M12"],
            "patterns": ["M\\d+", "螺栓|螺钉|螺母"]
        },
        "attributeExtraction": {
            "规格型号": {
                "type": "dimension",
                "patterns": ["M(\\d+)[×x](\\d+)", "M(\\d+)"],
                "required": True
            },
            "公称直径": {
                "type": "dimension",
                "unit": "mm",
                "patterns": ["M(\\d+)"],
                "required": True
            },
            "公称长度": {
                "type": "dimension",
                "unit": "mm",
                "patterns": ["[×x](\\d+)", "长度(\\d+)"],
                "required": False
            },
            "材质": {
                "type": "material",
                "patterns": ["(35CrMo|45#|Q235|304|316|碳钢|不锈钢)"],
                "defaultValue": "碳钢",
                "required": False
            },
            "性能等级": {
                "type": "performance",
                "patterns": ["([\\d.]+)级", "等级([\\d.]+)"],
                "allowedValues": ["4.8", "8.8", "10.9", "12.9"],
                "defaultValue": "8.8",
                "required": False
            }
        },
        "tables": {
            "dimension_table": {
                "description": "螺栓尺寸表",
                "columns": ["公称直径", "螺纹长度", "头部高度"],
                "data": [
                    ["M6", 18, 4.0],
                    ["M8", 22, 5.3],
                    ["M10", 26, 6.4],
                    ["M12", 30, 7.5],
                    ["M16", 38, 10.0],
                    ["M20", 46, 12.5]
                ]
            }
        },
        "categoryMapping": {
            "primaryCategory": "紧固件",
            "secondaryCategory": "螺栓",
            "tertiaryCategory": "六角头螺栓",
            "categoryId": "CAT_FASTENER_001"
        },
        "outputStructure": {
            "物料名称": "六角头螺栓 {规格型号}",
            "类目": "{primaryCategory}/{secondaryCategory}/{tertiaryCategory}",
            "规格参数": {
                "规格": "{规格型号}",
                "公称直径": "{公称直径}",
                "公称长度": "{公称长度}",
                "材质": "{材质}",
                "性能等级": "{性能等级}"
            },
            "适用标准": "{standardCode}"
        },
        "fallbackStrategy": {
            "lowConfidenceThreshold": 0.6,
            "humanReviewRequired": True
        }
    }
}


class SkillCompiler:
    """Skill编译器 (Mock模式)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _detect_domain(self, standard: Standard) -> str:
        """检测国标所属领域"""
        code = standard.standard_code.lower()
        name = standard.standard_name.lower()
        
        # 管材领域关键词
        pipe_keywords = ["管", "管道", "管材", "pvc", "pe", "ppr", "4219"]
        for kw in pipe_keywords:
            if kw in code or kw in name:
                return "pipe"
        
        # 紧固件领域关键词
        fastener_keywords = ["螺栓", "螺钉", "螺母", "紧固", "5782", "5783"]
        for kw in fastener_keywords:
            if kw in code or kw in name:
                return "fastener"
        
        return "general"
    
    def _generate_skill_id(self, standard: Standard) -> str:
        """生成Skill ID"""
        code = standard.standard_code.replace("/", "_").replace(".", "_").replace("-", "_").lower()
        return f"skill_{code}"
    
    async def compile(self, standard: Standard) -> Skill:
        """编译国标为Skill"""
        # 检测领域
        domain = self._detect_domain(standard)
        
        # 获取模板
        template = SKILL_TEMPLATES.get(domain, SKILL_TEMPLATES.get("pipe")).copy()
        
        # 定制DSL
        skill_id = self._generate_skill_id(standard)
        template["skillId"] = skill_id
        template["skillName"] = f"{standard.standard_name} Skill"
        template["standardCode"] = standard.standard_code
        template["domain"] = domain
        
        # 创建Skill记录
        skill = Skill(
            skill_id=skill_id,
            skill_name=template["skillName"],
            standard_id=standard.id,
            domain=domain,
            priority=template.get("priority", 100),
            applicable_material_types=template.get("applicableMaterialTypes", []),
            dsl_content=template,
            dsl_version="1.0.0",
            status=SkillStatus.DRAFT
        )
        
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        
        return skill
