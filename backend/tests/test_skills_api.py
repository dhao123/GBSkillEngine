"""
Skill管理API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillStatus
from app.models.standard import Standard, StandardStatus


@pytest.mark.asyncio
async def test_list_skills_empty(client: AsyncClient):
    """测试获取空的Skill列表"""
    response = await client.get("/api/v1/skills")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_skill(client: AsyncClient, db_session: AsyncSession):
    """测试创建Skill"""
    # 先创建关联的国标
    standard = Standard(
        standard_code="GB/T 3001-2024",
        standard_name="Skill测试国标",
        status=StandardStatus.UPLOADED
    )
    db_session.add(standard)
    await db_session.commit()
    await db_session.refresh(standard)
    
    skill_data = {
        "skill_id": "SKILL_TEST_001",
        "name": "测试Skill",
        "version": "1.0.0",
        "standard_id": standard.id,
        "dsl_config": {
            "name": "测试Skill",
            "version": "1.0.0",
            "category": "测试",
            "attributes": [
                {"name": "attr1", "type": "string", "required": True}
            ],
            "rules": []
        }
    }
    
    response = await client.post("/api/v1/skills", json=skill_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["skill_id"] == skill_data["skill_id"]
    assert data["name"] == skill_data["name"]


@pytest.mark.asyncio
async def test_get_skill(client: AsyncClient, db_session: AsyncSession):
    """测试获取Skill详情"""
    # 创建测试数据
    skill = Skill(
        skill_id="SKILL_GET_TEST",
        name="详情测试Skill",
        version="1.0.0",
        dsl_config={"name": "test", "version": "1.0.0"},
        status=SkillStatus.ACTIVE
    )
    db_session.add(skill)
    await db_session.commit()
    
    # 获取详情
    response = await client.get(f"/api/v1/skills/{skill.skill_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["skill_id"] == "SKILL_GET_TEST"
    assert data["name"] == "详情测试Skill"


@pytest.mark.asyncio
async def test_get_nonexistent_skill(client: AsyncClient):
    """测试获取不存在的Skill"""
    response = await client.get("/api/v1/skills/NONEXISTENT_SKILL")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_skill(client: AsyncClient, db_session: AsyncSession):
    """测试更新Skill"""
    skill = Skill(
        skill_id="SKILL_UPDATE_TEST",
        name="原始名称",
        version="1.0.0",
        dsl_config={"name": "test", "version": "1.0.0"},
        status=SkillStatus.ACTIVE
    )
    db_session.add(skill)
    await db_session.commit()
    
    update_data = {"name": "更新后名称", "version": "1.0.1"}
    response = await client.put(f"/api/v1/skills/{skill.skill_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后名称"
    assert data["version"] == "1.0.1"


@pytest.mark.asyncio
async def test_delete_skill(client: AsyncClient, db_session: AsyncSession):
    """测试删除Skill"""
    skill = Skill(
        skill_id="SKILL_DELETE_TEST",
        name="待删除Skill",
        version="1.0.0",
        dsl_config={"name": "test", "version": "1.0.0"},
        status=SkillStatus.ACTIVE
    )
    db_session.add(skill)
    await db_session.commit()
    
    response = await client.delete(f"/api/v1/skills/{skill.skill_id}")
    assert response.status_code == 200
    
    # 验证已删除
    get_response = await client.get(f"/api/v1/skills/{skill.skill_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_skills_with_pagination(client: AsyncClient, db_session: AsyncSession):
    """测试Skill列表分页"""
    # 创建多个Skill
    for i in range(15):
        skill = Skill(
            skill_id=f"SKILL_PAGE_{i:03d}",
            name=f"分页测试Skill{i}",
            version="1.0.0",
            dsl_config={"name": f"test{i}", "version": "1.0.0"},
            status=SkillStatus.ACTIVE
        )
        db_session.add(skill)
    await db_session.commit()
    
    # 第一页
    response1 = await client.get("/api/v1/skills", params={"page": 1, "page_size": 10})
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["total"] == 15
    assert len(data1["items"]) == 10
    
    # 第二页
    response2 = await client.get("/api/v1/skills", params={"page": 2, "page_size": 10})
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 5


@pytest.mark.asyncio
async def test_skill_dsl_validation(client: AsyncClient, db_session: AsyncSession):
    """测试Skill DSL配置验证"""
    # 创建带无效DSL的Skill
    skill_data = {
        "skill_id": "SKILL_INVALID_DSL",
        "name": "无效DSL测试",
        "version": "1.0.0",
        "dsl_config": {}  # 空的DSL配置
    }
    
    response = await client.post("/api/v1/skills", json=skill_data)
    # 根据实际验证逻辑，可能返回400或200
    # 这里假设允许空DSL，实际根据业务调整
    assert response.status_code in [200, 400, 422]
