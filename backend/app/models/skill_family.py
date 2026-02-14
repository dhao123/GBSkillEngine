"""
GBSkillEngine 技能族(SkillFamily)模型

SkillFamily是从StandardSeries派生的聚合实体。
同一个标准系列下的所有国标生成的Skills归为同一个技能族。
例如：GB/T 4219系列下的4219.1, 4219.2, 4219.3各自生成的Skill都属于同一SkillFamily。
"""
from typing import List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SkillFamily(Base):
    """
    技能族表 - 聚合同一系列标准生成的Skills
    
    与StandardSeries是1:1关系，每个标准系列自动对应一个技能族。
    """
    __tablename__ = "skill_families"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    family_code = Column(String(100), unique=True, nullable=False, index=True,
                        comment="技能族编码，通常与series_code对应")
    family_name = Column(String(500), nullable=False,
                        comment="技能族名称")
    series_id = Column(Integer, ForeignKey("standard_series.id"), nullable=True,
                      comment="关联的标准系列ID")
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True,
                      comment="所属领域ID")
    description = Column(Text, nullable=True,
                        comment="技能族描述")
    skill_count = Column(Integer, default=0,
                        comment="族内Skill数量")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                       comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), comment="更新时间")
    
    # 关系
    series = relationship("StandardSeries", back_populates="skill_family")
    domain = relationship("Domain")
    members = relationship("SkillFamilyMember", back_populates="family", 
                          cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SkillFamily {self.family_code}: {self.family_name}>"
    
    def get_skills(self, db_session) -> List:
        """获取族内所有Skills"""
        from app.models.skill import Skill
        skill_ids = [m.skill_id for m in self.members]
        return db_session.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    
    @classmethod
    def get_or_create_from_series(cls, db_session, series) -> "SkillFamily":
        """
        从StandardSeries创建或获取对应的SkillFamily
        
        Args:
            db_session: 数据库会话
            series: StandardSeries对象
            
        Returns:
            SkillFamily: 技能族对象
        """
        # 检查是否已存在
        existing = db_session.query(cls).filter(cls.series_id == series.id).first()
        if existing:
            return existing
        
        # 创建新的技能族
        family_code = f"family_{series.series_code.replace('/', '_').replace(' ', '')}"
        new_family = cls(
            family_code=family_code,
            family_name=f"{series.series_name or series.series_code} 技能族",
            series_id=series.id,
            domain_id=series.domain_id
        )
        db_session.add(new_family)
        db_session.flush()
        return new_family


class SkillFamilyMember(Base):
    """
    技能族成员关联表
    
    记录Skill与SkillFamily的多对多关系（虽然通常是1:1）。
    保留为独立表以支持未来可能的多族归属场景。
    """
    __tablename__ = "skill_family_members"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    family_id = Column(Integer, ForeignKey("skill_families.id"), nullable=False,
                      comment="技能族ID")
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False,
                     comment="Skill ID")
    role = Column(String(50), default="member",
                 comment="在族中的角色：primary(主技能), member(成员)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                       comment="创建时间")
    
    # 关系
    family = relationship("SkillFamily", back_populates="members")
    skill = relationship("Skill", back_populates="family_memberships")
    
    def __repr__(self):
        return f"<SkillFamilyMember family={self.family_id} skill={self.skill_id}>"
