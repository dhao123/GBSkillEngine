"""
GBSkillEngine 示例数据初始化脚本

运行方式: python -m app.utils.init_sample_data
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker, init_db
from app.models.standard import Standard, StandardStatus
from app.models.skill import Skill, SkillStatus


SAMPLE_STANDARDS = [
    {
        "standard_code": "GB/T 4219.1-2021",
        "standard_name": "工业用聚氯乙烯(PVC-U)管道系统 第1部分:管材",
        "version_year": "2021",
        "domain": "pipe",
        "product_scope": "适用于工业输送液体(包括压力输送和非压力输送)、输送气体以及作为结构材料使用的硬聚氯乙烯管材",
        "status": StandardStatus.COMPILED
    },
    {
        "standard_code": "GB/T 10002.1-2006",
        "standard_name": "给水用硬聚氯乙烯(PVC-U)管材",
        "version_year": "2006",
        "domain": "pipe",
        "product_scope": "适用于一般输送水的给水系统用的硬聚氯乙烯管材",
        "status": StandardStatus.UPLOADED
    },
    {
        "standard_code": "GB/T 5782-2016",
        "standard_name": "六角头螺栓 C级",
        "version_year": "2016",
        "domain": "fastener",
        "product_scope": "适用于一般机械紧固用的C级六角头螺栓",
        "status": StandardStatus.COMPILED
    },
]


SAMPLE_SKILLS = [
    {
        "skill_id": "skill_gb_t_4219_1_2021",
        "skill_name": "工业用PVC-U管道系统 Skill",
        "domain": "pipe",
        "priority": 100,
        "applicable_material_types": ["UPVC管", "PVC-U管", "工业管"],
        "status": SkillStatus.ACTIVE,
        "dsl_content": {
            "skillId": "skill_gb_t_4219_1_2021",
            "skillName": "工业用PVC-U管道系统 GB/T 4219.1-2021",
            "version": "1.0.0",
            "standardCode": "GB/T 4219.1-2021",
            "domain": "pipe",
            "applicableMaterialTypes": ["UPVC管", "PVC-U管", "工业管", "塑料管"],
            "priority": 100,
            "intentRecognition": {
                "keywords": ["UPVC", "PVC-U", "工业管", "管材", "DN", "PN"],
                "patterns": ["(UPVC|PVC-U)", "(DN|dn)\\d+", "(PN|pn)[\\d.]+"]
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
                    "patterns": ["PN([\\d.]+)", "pn([\\d.]+)"],
                    "required": False
                },
                "材质": {
                    "type": "material",
                    "patterns": ["(UPVC|PVC-U|PVC)"],
                    "defaultValue": "PVC-U",
                    "required": False
                },
                "管系列": {
                    "type": "dimension",
                    "patterns": ["S(\\d+)"],
                    "required": False
                }
            },
            "tables": {
                "dn_outer_diameter_map": {
                    "description": "公称直径与外径映射表",
                    "columns": ["DN", "外径(mm)"],
                    "data": [
                        [20, 25], [25, 32], [32, 40], [40, 50], [50, 63],
                        [65, 75], [80, 90], [100, 110], [125, 140], [150, 160],
                        [200, 225], [250, 280], [300, 315]
                    ]
                },
                "dimension_table": {
                    "description": "尺寸规格表",
                    "columns": ["DN", "外径", "PN0.6壁厚", "PN1.0壁厚", "PN1.6壁厚"],
                    "data": [
                        [50, 63, 1.9, 2.0, 3.0],
                        [65, 75, 2.3, 2.9, 3.6],
                        [80, 90, 2.8, 3.5, 4.3],
                        [100, 110, 3.4, 4.2, 5.3],
                        [125, 140, 4.3, 5.4, 6.7],
                        [150, 160, 4.9, 6.2, 7.7],
                        [200, 225, 6.9, 8.6, 10.8]
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
                "物料名称": "{材质}管 DN{公称直径}",
                "类目": "{primaryCategory}/{secondaryCategory}/{tertiaryCategory}",
                "规格参数": {
                    "公称直径DN": "{公称直径}",
                    "公称外径": "{外径}",
                    "公称压力PN": "{公称压力}",
                    "最小壁厚": "{壁厚}",
                    "材质": "{材质}"
                },
                "适用标准": "GB/T 4219.1-2021"
            },
            "fallbackStrategy": {
                "lowConfidenceThreshold": 0.6,
                "humanReviewRequired": True
            }
        }
    },
    {
        "skill_id": "skill_gb_t_5782_2016",
        "skill_name": "六角头螺栓 C级 Skill",
        "domain": "fastener",
        "priority": 100,
        "applicable_material_types": ["螺栓", "六角头螺栓", "紧固件"],
        "status": SkillStatus.ACTIVE,
        "dsl_content": {
            "skillId": "skill_gb_t_5782_2016",
            "skillName": "六角头螺栓 C级 GB/T 5782-2016",
            "version": "1.0.0",
            "standardCode": "GB/T 5782-2016",
            "domain": "fastener",
            "applicableMaterialTypes": ["螺栓", "六角头螺栓", "紧固件"],
            "priority": 100,
            "intentRecognition": {
                "keywords": ["螺栓", "六角头", "M6", "M8", "M10", "M12"],
                "patterns": ["M\\d+", "螺栓"]
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
                    "patterns": ["[×x](\\d+)"],
                    "required": False
                },
                "材质": {
                    "type": "material",
                    "patterns": ["(35CrMo|45#|碳钢|不锈钢)"],
                    "defaultValue": "碳钢",
                    "required": False
                },
                "性能等级": {
                    "type": "performance",
                    "patterns": ["([\\d.]+)级"],
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
                        ["M12", 30, 7.5]
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
                "适用标准": "GB/T 5782-2016"
            },
            "fallbackStrategy": {
                "lowConfidenceThreshold": 0.6,
                "humanReviewRequired": True
            }
        }
    }
]


async def init_sample_data():
    """初始化示例数据"""
    print("正在初始化数据库...")
    await init_db()
    
    async with async_session_maker() as session:
        # 添加示例国标
        print("添加示例国标...")
        for std_data in SAMPLE_STANDARDS:
            standard = Standard(**std_data)
            session.add(standard)
        
        await session.commit()
        
        # 获取国标ID
        from sqlalchemy import select
        result = await session.execute(select(Standard))
        standards = {s.standard_code: s.id for s in result.scalars().all()}
        
        # 添加示例Skill
        print("添加示例Skill...")
        for skill_data in SAMPLE_SKILLS:
            # 关联国标
            standard_code = skill_data["dsl_content"].get("standardCode")
            if standard_code and standard_code in standards:
                skill_data["standard_id"] = standards[standard_code]
            
            skill = Skill(**skill_data)
            session.add(skill)
        
        await session.commit()
        
        print("示例数据初始化完成!")
        print(f"  - 添加了 {len(SAMPLE_STANDARDS)} 个国标")
        print(f"  - 添加了 {len(SAMPLE_SKILLS)} 个Skill")


if __name__ == "__main__":
    asyncio.run(init_sample_data())
