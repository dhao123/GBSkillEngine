"""
国标管理API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.standard import Standard, StandardStatus


@pytest.mark.asyncio
async def test_list_standards_empty(client: AsyncClient):
    """测试获取空的国标列表"""
    response = await client.get("/api/v1/standards")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_standard(client: AsyncClient, db_session: AsyncSession):
    """测试创建国标"""
    standard_data = {
        "standard_code": "GB/T 1234-2024",
        "standard_name": "测试国标",
        "version_year": "2024",
        "domain": "机械",
        "product_scope": "测试产品"
    }
    
    response = await client.post("/api/v1/standards", json=standard_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["standard_code"] == standard_data["standard_code"]
    assert data["standard_name"] == standard_data["standard_name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_standard(client: AsyncClient, db_session: AsyncSession):
    """测试创建重复国标"""
    standard_data = {
        "standard_code": "GB/T 5678-2024",
        "standard_name": "测试国标",
        "version_year": "2024"
    }
    
    # 第一次创建
    response1 = await client.post("/api/v1/standards", json=standard_data)
    assert response1.status_code == 200
    
    # 第二次创建应失败
    response2 = await client.post("/api/v1/standards", json=standard_data)
    assert response2.status_code == 400


@pytest.mark.asyncio
async def test_get_standard(client: AsyncClient, db_session: AsyncSession):
    """测试获取国标详情"""
    # 先创建
    standard = Standard(
        standard_code="GB/T 9999-2024",
        standard_name="详情测试国标",
        status=StandardStatus.UPLOADED
    )
    db_session.add(standard)
    await db_session.commit()
    await db_session.refresh(standard)
    
    # 获取详情
    response = await client.get(f"/api/v1/standards/{standard.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["standard_code"] == "GB/T 9999-2024"
    assert data["standard_name"] == "详情测试国标"


@pytest.mark.asyncio
async def test_get_nonexistent_standard(client: AsyncClient):
    """测试获取不存在的国标"""
    response = await client.get("/api/v1/standards/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_standard(client: AsyncClient, db_session: AsyncSession):
    """测试更新国标"""
    # 先创建
    standard = Standard(
        standard_code="GB/T 8888-2024",
        standard_name="原始名称",
        status=StandardStatus.UPLOADED
    )
    db_session.add(standard)
    await db_session.commit()
    await db_session.refresh(standard)
    
    # 更新
    update_data = {"standard_name": "更新后名称"}
    response = await client.put(f"/api/v1/standards/{standard.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["standard_name"] == "更新后名称"


@pytest.mark.asyncio
async def test_delete_standard(client: AsyncClient, db_session: AsyncSession):
    """测试删除国标"""
    # 先创建
    standard = Standard(
        standard_code="GB/T 7777-2024",
        standard_name="待删除国标",
        status=StandardStatus.UPLOADED
    )
    db_session.add(standard)
    await db_session.commit()
    await db_session.refresh(standard)
    
    # 删除
    response = await client.delete(f"/api/v1/standards/{standard.id}")
    
    assert response.status_code == 200
    
    # 验证已删除
    get_response = await client.get(f"/api/v1/standards/{standard.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_standards_with_filter(client: AsyncClient, db_session: AsyncSession):
    """测试带筛选条件的国标列表"""
    # 创建多个国标
    standards = [
        Standard(standard_code="GB/T 1001-2024", standard_name="机械国标1", domain="机械", status=StandardStatus.UPLOADED),
        Standard(standard_code="GB/T 1002-2024", standard_name="机械国标2", domain="机械", status=StandardStatus.COMPILED),
        Standard(standard_code="GB/T 2001-2024", standard_name="电气国标1", domain="电气", status=StandardStatus.UPLOADED),
    ]
    for s in standards:
        db_session.add(s)
    await db_session.commit()
    
    # 按domain筛选
    response = await client.get("/api/v1/standards", params={"domain": "机械"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    
    # 按status筛选
    response2 = await client.get("/api/v1/standards", params={"status": "compiled"})
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total"] == 1
    
    # 按keyword搜索
    response3 = await client.get("/api/v1/standards", params={"keyword": "电气"})
    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["total"] == 1
