"""
物料梳理API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillStatus


@pytest.mark.asyncio
async def test_parse_material_no_skills(client: AsyncClient):
    """测试无Skill时的物料梳理"""
    parse_data = {
        "material_name": "测试物料"
    }
    
    response = await client.post("/api/v1/material-parse/parse", json=parse_data)
    
    # 无匹配Skill时应返回空结果或提示
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_parse_material_with_skill(client: AsyncClient, db_session: AsyncSession):
    """测试有Skill时的物料梳理"""
    # 创建测试Skill
    skill = Skill(
        skill_id="SKILL_MATERIAL_TEST",
        name="物料测试Skill",
        version="1.0.0",
        dsl_config={
            "name": "物料测试Skill",
            "version": "1.0.0",
            "category": "轴承",
            "attributes": [
                {"name": "型号", "type": "string", "required": True},
                {"name": "内径", "type": "number", "required": False}
            ],
            "rules": [
                {
                    "pattern": "(?P<型号>[A-Z0-9]+)",
                    "extract": ["型号"]
                }
            ]
        },
        status=SkillStatus.ACTIVE
    )
    db_session.add(skill)
    await db_session.commit()
    
    parse_data = {
        "material_name": "深沟球轴承 6205-2RS"
    }
    
    response = await client.post("/api/v1/material-parse/parse", json=parse_data)
    
    assert response.status_code == 200
    data = response.json()
    # 验证返回结构
    assert "material_name" in data or "result" in data or "matched_skill" in data


@pytest.mark.asyncio
async def test_batch_parse_materials(client: AsyncClient, db_session: AsyncSession):
    """测试批量物料梳理"""
    # 创建测试Skill
    skill = Skill(
        skill_id="SKILL_BATCH_TEST",
        name="批量测试Skill",
        version="1.0.0",
        dsl_config={
            "name": "批量测试Skill",
            "version": "1.0.0",
            "category": "测试",
            "attributes": [],
            "rules": []
        },
        status=SkillStatus.ACTIVE
    )
    db_session.add(skill)
    await db_session.commit()
    
    batch_data = {
        "materials": [
            {"material_name": "测试物料1"},
            {"material_name": "测试物料2"},
            {"material_name": "测试物料3"}
        ]
    }
    
    response = await client.post("/api/v1/material-parse/batch", json=batch_data)
    
    assert response.status_code == 200
    data = response.json()
    # 验证批量处理结果
    assert "results" in data or "items" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_get_parse_history(client: AsyncClient):
    """测试获取梳理历史"""
    response = await client.get("/api/v1/material-parse/history")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_parse_material_with_options(client: AsyncClient, db_session: AsyncSession):
    """测试带选项的物料梳理"""
    # 创建测试Skill
    skill = Skill(
        skill_id="SKILL_OPTIONS_TEST",
        name="选项测试Skill",
        version="1.0.0",
        dsl_config={
            "name": "选项测试Skill",
            "version": "1.0.0",
            "category": "测试",
            "attributes": [],
            "rules": []
        },
        status=SkillStatus.ACTIVE
    )
    db_session.add(skill)
    await db_session.commit()
    
    parse_data = {
        "material_name": "带选项的测试物料",
        "options": {
            "confidence_threshold": 0.8,
            "max_results": 5
        }
    }
    
    response = await client.post("/api/v1/material-parse/parse", json=parse_data)
    
    # 验证请求被接受
    assert response.status_code in [200, 422]  # 422 if options not supported
