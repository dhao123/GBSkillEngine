"""
GBSkillEngine Skill数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
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
    domain = Column(String(100), nullable=True, index=True, comment="领域(已废弃，保留兼容)")
    priority = Column(Integer, default=100, comment="优先级")
    applicable_material_types = Column(JSON, nullable=True, comment="适用物料类型")
    dsl_content = Column(JSON, nullable=False, comment="Skill DSL内容")
    dsl_version = Column(String(20), default="1.0.0", comment="DSL版本号")
    # 使用 String 替代 SQLEnum，避免 PostgreSQL ENUM 类型大小写映射问题
    status = Column(String(20), default=SkillStatus.DRAFT.value, comment="状态")
    
    # 新增外键关联 - 迁移后启用
    # 注意: 这些列需要运行 alembic upgrade head 后才存在
    domain_id = Column(Integer, ForeignKey("domains.id", use_alter=True, name="fk_skill_domain"), nullable=True,
                      comment="所属领域ID")
    category_id = Column(Integer, ForeignKey("categories.id", use_alter=True, name="fk_skill_category"), nullable=True,
                        comment="所属类目ID")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    # 关系 - 使用lazy加载避免表不存在时报错
    standard = relationship("Standard", backref="skills")
    domain_ref = relationship("Domain", back_populates="skills", lazy="select")
    category = relationship("Category", back_populates="skills", lazy="select")
    family_memberships = relationship("SkillFamilyMember", back_populates="skill",
                                     cascade="all, delete-orphan", lazy="select")
    
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
