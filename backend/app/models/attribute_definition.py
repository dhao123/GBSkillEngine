"""
GBSkillEngine 属性定义(AttributeDefinition)模型

AttributeDefinition存储从国标文件中提取的属性定义。
属性可以跨领域复用，通过DomainAttribute关联表管理领域-属性关系。
"""
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AttributeDefinition(Base):
    """
    属性定义表 - 存储从国标提取的属性元数据
    
    属性定义是全局共享的，通过DomainAttribute关联到具体领域。
    支持去重和复用：相同名称的属性合并patterns，增加usage_count。
    """
    __tablename__ = "attribute_definitions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    attribute_code = Column(String(100), unique=True, nullable=False, index=True,
                           comment="属性编码，如 outer_diameter, wall_thickness")
    attribute_name = Column(String(200), nullable=False,
                           comment="属性名称，如 外径, 壁厚")
    attribute_name_en = Column(String(200), nullable=True,
                              comment="英文名称")
    data_type = Column(String(50), default="string",
                      comment="数据类型：string, number, enum, range, boolean")
    unit = Column(String(50), nullable=True,
                 comment="单位，如 mm, kg, MPa")
    patterns = Column(JSON, nullable=True,
                     comment="提取模式列表，用于从原文匹配属性值")
    synonyms = Column(JSON, nullable=True,
                     comment="同义词列表，如 [外径, 公称外径, OD]")
    validation_rules = Column(JSON, nullable=True,
                             comment="校验规则，如 {min: 0, max: 1000}")
    description = Column(Text, nullable=True,
                        comment="属性描述")
    usage_count = Column(Integer, default=1,
                        comment="被引用次数，用于评估属性重要性")
    is_common = Column(Boolean, default=False,
                      comment="是否为通用属性（跨多领域使用）")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                       comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), comment="更新时间")
    
    # 关系
    domain_attributes = relationship("DomainAttribute", back_populates="attribute",
                                    cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AttributeDefinition {self.attribute_code}: {self.attribute_name}>"
    
    def get_domains(self, db_session):
        """获取使用此属性的所有领域"""
        from app.models.domain import Domain
        domain_ids = [da.domain_id for da in self.domain_attributes]
        return db_session.query(Domain).filter(Domain.id.in_(domain_ids)).all()
    
    def merge_patterns(self, new_patterns: List[str]) -> None:
        """
        合并新的提取模式
        
        Args:
            new_patterns: 新的模式列表
        """
        existing = set(self.patterns or [])
        for pattern in new_patterns:
            existing.add(pattern)
        self.patterns = list(existing)
        self.usage_count += 1
    
    @classmethod
    def get_or_create(cls, db_session, attribute_code: str, attribute_name: str,
                      data_type: str = "string", unit: Optional[str] = None,
                      patterns: Optional[List[str]] = None) -> "AttributeDefinition":
        """
        获取或创建属性定义（支持去重合并）
        
        Args:
            db_session: 数据库会话
            attribute_code: 属性编码
            attribute_name: 属性名称
            data_type: 数据类型
            unit: 单位
            patterns: 提取模式
            
        Returns:
            AttributeDefinition: 属性定义对象
        """
        existing = db_session.query(cls).filter(cls.attribute_code == attribute_code).first()
        if existing:
            # 合并patterns并增加usage_count
            if patterns:
                existing.merge_patterns(patterns)
            return existing
        
        new_attr = cls(
            attribute_code=attribute_code,
            attribute_name=attribute_name,
            data_type=data_type,
            unit=unit,
            patterns=patterns or []
        )
        db_session.add(new_attr)
        db_session.flush()
        return new_attr


class DomainAttribute(Base):
    """
    领域-属性关联表
    
    记录属性在特定领域中的使用情况和配置。
    同一属性在不同领域中可能有不同的优先级和默认值。
    """
    __tablename__ = "domain_attributes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False,
                      comment="领域ID")
    attribute_id = Column(Integer, ForeignKey("attribute_definitions.id"), nullable=False,
                         comment="属性定义ID")
    priority = Column(Integer, default=100,
                     comment="在该领域中的优先级，数值越小优先级越高")
    is_required = Column(Boolean, default=False,
                        comment="是否为该领域的必填属性")
    default_value = Column(String(500), nullable=True,
                          comment="在该领域中的默认值")
    domain_specific_rules = Column(JSON, nullable=True,
                                  comment="领域特定的校验规则")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                       comment="创建时间")
    
    # 关系
    domain = relationship("Domain", back_populates="attributes")
    attribute = relationship("AttributeDefinition", back_populates="domain_attributes")
    
    def __repr__(self):
        return f"<DomainAttribute domain={self.domain_id} attr={self.attribute_id}>"
    
    @classmethod
    def link_attribute_to_domain(cls, db_session, domain_id: int, 
                                  attribute_id: int, priority: int = 100,
                                  is_required: bool = False) -> "DomainAttribute":
        """
        将属性关联到领域
        
        Args:
            db_session: 数据库会话
            domain_id: 领域ID
            attribute_id: 属性定义ID
            priority: 优先级
            is_required: 是否必填
            
        Returns:
            DomainAttribute: 关联对象
        """
        existing = db_session.query(cls).filter(
            cls.domain_id == domain_id,
            cls.attribute_id == attribute_id
        ).first()
        if existing:
            return existing
        
        new_link = cls(
            domain_id=domain_id,
            attribute_id=attribute_id,
            priority=priority,
            is_required=is_required
        )
        db_session.add(new_link)
        db_session.flush()
        
        # 更新属性的is_common标记
        attr = db_session.query(AttributeDefinition).get(attribute_id)
        if attr:
            domain_count = db_session.query(cls).filter(
                cls.attribute_id == attribute_id
            ).count()
            attr.is_common = domain_count >= 2
        
        return new_link
