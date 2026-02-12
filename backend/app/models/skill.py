"""
GBSkillEngine Skill数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class SkillStatus(str, enum.Enum):
    """Skill状态枚举"""
    DRAFT = "draft"           # 草稿
    TESTING = "testing"       # 测试中
    ACTIVE = "active"         # 已激活
    DEPRECATED = "deprecated" # 已废弃


class Skill(Base):
    """Skill定义表"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_id = Column(String(200), unique=True, nullable=False, index=True, comment="Skill唯一标识")
    skill_name = Column(String(500), nullable=False, comment="Skill名称")
    standard_id = Column(Integer, ForeignKey("standards.id"), nullable=True, comment="关联的国标ID")
    domain = Column(String(100), nullable=True, index=True, comment="领域")
    priority = Column(Integer, default=100, comment="优先级")
    applicable_material_types = Column(JSON, nullable=True, comment="适用物料类型")
    dsl_content = Column(JSON, nullable=False, comment="Skill DSL内容")
    dsl_version = Column(String(20), default="1.0.0", comment="DSL版本号")
    status = Column(SQLEnum(SkillStatus), default=SkillStatus.DRAFT, comment="状态")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    # 关系
    standard = relationship("Standard", backref="skills")
    
    def __repr__(self):
        return f"<Skill {self.skill_id}: {self.skill_name}>"


class SkillVersion(Base):
    """Skill版本表"""
    __tablename__ = "skill_versions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, comment="关联的Skill ID")
    version = Column(String(20), nullable=False, comment="版本号")
    dsl_content = Column(JSON, nullable=False, comment="该版本的DSL内容")
    change_log = Column(Text, nullable=True, comment="变更日志")
    is_active = Column(Boolean, default=False, comment="是否为当前激活版本")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    # 关系
    skill = relationship("Skill", backref="versions")
    
    def __repr__(self):
        return f"<SkillVersion {self.skill_id} v{self.version}>"
