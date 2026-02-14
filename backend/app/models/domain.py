"""
GBSkillEngine 领域(Domain)模型

Domain是动态推断的实体，由LLM分析国标文件内容后自动创建。
领域的颜色和扇区角度由系统自动分配，不再预置硬编码。
"""
from typing import List, Tuple
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# 动态颜色调色板 - 用于自动分配领域颜色
DOMAIN_PALETTE: List[str] = [
    "#00d4ff",  # 青蓝色
    "#ff6b6b",  # 珊瑚红
    "#7c3aed",  # 紫罗兰
    "#10b981",  # 翠绿色
    "#f59e0b",  # 琥珀色
    "#ec4899",  # 粉红色
    "#06b6d4",  # 天蓝色
    "#84cc16",  # 柠檬绿
    "#f97316",  # 橙色
    "#8b5cf6",  # 薰衣草紫
    "#14b8a6",  # 青色
    "#ef4444",  # 红色
]


def allocate_domain_visual(domain_count: int) -> Tuple[str, float]:
    """
    为新领域分配视觉属性（颜色和扇区角度）
    
    Args:
        domain_count: 当前已有的领域数量（不含即将创建的）
        
    Returns:
        tuple: (color, sector_angle)
            - color: 十六进制颜色值
            - sector_angle: 在3D图谱中的扇区角度
            
    Example:
        >>> allocate_domain_visual(0)
        ("#00d4ff", 0.0)
        >>> allocate_domain_visual(3)
        ("#10b981", 90.0)
    """
    color = DOMAIN_PALETTE[domain_count % len(DOMAIN_PALETTE)]
    # 扇区角度均匀分布在360度圆周上
    sector_angle = (360.0 / max(domain_count + 1, 1)) * domain_count
    return color, sector_angle


class Domain(Base):
    """
    领域表 - 动态推断的一级分类
    
    领域是由LLM分析国标文件内容后自动创建的，不再预置硬编码。
    每个领域有唯一的颜色和在3D知识图谱中的扇区位置。
    """
    __tablename__ = "domains"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain_code = Column(String(50), unique=True, nullable=False, index=True,
                        comment="领域编码，如 pipe, valve, bearing")
    domain_name = Column(String(200), nullable=False,
                        comment="领域名称，如 管材管件、阀门、轴承")
    color = Column(String(20), nullable=False,
                  comment="领域颜色，十六进制格式")
    sector_angle = Column(Float, default=0.0,
                         comment="在3D图谱中的扇区起始角度")
    description = Column(Text, nullable=True,
                        comment="领域描述")
    standard_count = Column(Integer, default=0,
                           comment="该领域下的国标数量")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                       comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), comment="更新时间")
    
    # 关系
    series = relationship("StandardSeries", back_populates="domain")
    standards = relationship("Standard", back_populates="domain_ref")
    categories = relationship("Category", back_populates="domain")
    skills = relationship("Skill", back_populates="domain_ref")
    attributes = relationship("DomainAttribute", back_populates="domain")
    
    def __repr__(self):
        return f"<Domain {self.domain_code}: {self.domain_name}>"
    
    @classmethod
    def get_or_create(cls, db_session, domain_code: str, domain_name: str) -> "Domain":
        """
        获取或创建领域
        
        Args:
            db_session: 数据库会话
            domain_code: 领域编码
            domain_name: 领域名称
            
        Returns:
            Domain: 领域对象
        """
        existing = db_session.query(cls).filter(cls.domain_code == domain_code).first()
        if existing:
            return existing
        
        # 统计当前领域数量，用于分配视觉属性
        current_count = db_session.query(cls).count()
        color, sector_angle = allocate_domain_visual(current_count)
        
        new_domain = cls(
            domain_code=domain_code,
            domain_name=domain_name,
            color=color,
            sector_angle=sector_angle
        )
        db_session.add(new_domain)
        db_session.flush()
        return new_domain
    
    @classmethod
    def recalculate_sector_angles(cls, db_session) -> None:
        """
        重新计算所有领域的扇区角度（领域增删后调用）
        
        Args:
            db_session: 数据库会话
        """
        domains = db_session.query(cls).order_by(cls.id).all()
        total = len(domains)
        for i, domain in enumerate(domains):
            domain.sector_angle = (360.0 / max(total, 1)) * i
        db_session.flush()
