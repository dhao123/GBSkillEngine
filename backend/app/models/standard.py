"""
GBSkillEngine 国标数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
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
    domain = Column(String(100), nullable=True, comment="适用领域")
    product_scope = Column(Text, nullable=True, comment="产品范围")
    file_path = Column(String(500), nullable=True, comment="文档存储路径")
    file_type = Column(String(20), nullable=True, comment="文档类型")
    file_hash = Column(String(64), nullable=True, comment="文件Hash")
    status = Column(SQLEnum(StandardStatus), default=StandardStatus.DRAFT, comment="状态")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    def __repr__(self):
        return f"<Standard {self.standard_code}: {self.standard_name}>"
