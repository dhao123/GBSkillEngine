"""
GBSkillEngine 国标数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class StandardStatus(str, enum.Enum):
    """国标状态枚举"""
    DRAFT = "draft"           # 草稿
    UPLOADED = "uploaded"     # 已上传
    COMPILED = "compiled"     # 已编译
    PUBLISHED = "published"   # 已发布
    DEPRECATED = "deprecated" # 已废弃


class Standard(Base):
    """国标元数据表"""
    __tablename__ = "standards"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    standard_code = Column(String(100), unique=True, nullable=False, index=True, comment="国标编号")
    standard_name = Column(String(500), nullable=False, comment="标准名称")
    version_year = Column(String(20), nullable=True, comment="版本年份")
    domain = Column(String(100), nullable=True, comment="适用领域(已废弃，保留兼容)")
    product_scope = Column(Text, nullable=True, comment="产品范围")
    file_path = Column(String(500), nullable=True, comment="文档存储路径")
    file_type = Column(String(20), nullable=True, comment="文档类型")
    file_hash = Column(String(64), nullable=True, comment="文件Hash")
    # 使用 String 替代 SQLEnum，避免 PostgreSQL ENUM 类型大小写映射问题
    status = Column(String(20), default=StandardStatus.DRAFT.value, comment="状态")
    
    # 新增外键关联 - 迁移后启用
    # 注意: 这些列需要运行 alembic upgrade head 后才存在
    series_id = Column(Integer, ForeignKey("standard_series.id", use_alter=True, name="fk_standard_series"), nullable=True, 
                      comment="所属标准系列ID")
    domain_id = Column(Integer, ForeignKey("domains.id", use_alter=True, name="fk_standard_domain"), nullable=True,
                      comment="所属领域ID")
    category_id = Column(Integer, ForeignKey("categories.id", use_alter=True, name="fk_standard_category"), nullable=True,
                        comment="所属类目ID")
    part_number = Column(Integer, nullable=True, comment="在系列中的分部编号")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    # 关系 - 使用lazy加载避免表不存在时报错
    series = relationship("StandardSeries", back_populates="standards", lazy="select")
    domain_ref = relationship("Domain", back_populates="standards", lazy="select")
    category = relationship("Category", back_populates="standards", lazy="select")
    
    def __repr__(self):
        return f"<Standard {self.standard_code}: {self.standard_name}>"
