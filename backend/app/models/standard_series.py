"""
GBSkillEngine 标准系列(StandardSeries)模型

StandardSeries是聚合相关国标文件的核心实体。
例如：GB/T 4219.1, GB/T 4219.2, GB/T 4219.3 属于同一个系列 "GB/T 4219"
"""
import re
from typing import Tuple, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


def detect_series(standard_code: str) -> Tuple[str, Optional[int]]:
    """
    从标准编号中提取系列信息
    
    Args:
        standard_code: 标准编号，如 "GB/T 4219.1-2021"
        
    Returns:
        tuple: (series_code, part_number)
            - series_code: 系列编号，如 "GB/T 4219"
            - part_number: 分部编号，如 1；若无则为 None
            
    Examples:
        >>> detect_series("GB/T 4219.1-2021")
        ("GB/T 4219", 1)
        >>> detect_series("GB/T 5782-2016")
        ("GB/T 5782", None)
        >>> detect_series("GB 50017-2017")
        ("GB 50017", None)
    """
    # 匹配格式: GB/T 数字.分部编号-年份 或 GB 数字-年份
    match = re.match(r'^(GB(?:/T)?\s*\d+)(?:\.(\d+))?', standard_code)
    if match:
        series_code = match.group(1)
        part_num = int(match.group(2)) if match.group(2) else None
        return series_code, part_num
    return standard_code, None


class StandardSeries(Base):
    """
    标准系列表 - 聚合相关国标文件
    
    一个系列包含多个具有相同编号前缀的国标文件。
    例如：GB/T 4219 系列包含 GB/T 4219.1, GB/T 4219.2, GB/T 4219.3
    """
    __tablename__ = "standard_series"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    series_code = Column(String(100), unique=True, nullable=False, index=True, 
                        comment="系列编号，如 GB/T 4219")
    series_name = Column(String(500), nullable=True, 
                        comment="系列名称，由首个标准的产品范围推断")
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True, 
                      comment="所属领域ID")
    part_count = Column(Integer, default=1, comment="系列包含的分部数量")
    description = Column(Text, nullable=True, comment="系列描述")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       onupdate=func.now(), comment="更新时间")
    
    # 关系
    domain = relationship("Domain", back_populates="series")
    standards = relationship("Standard", back_populates="series")
    skill_family = relationship("SkillFamily", back_populates="series", uselist=False)
    
    def __repr__(self):
        return f"<StandardSeries {self.series_code}: {self.series_name}>"
    
    @classmethod
    def get_or_create_from_code(cls, db_session, standard_code: str) -> "StandardSeries":
        """
        从标准编号获取或创建对应的系列
        
        Args:
            db_session: 数据库会话
            standard_code: 标准编号
            
        Returns:
            StandardSeries: 系列对象
        """
        series_code, _ = detect_series(standard_code)
        
        existing = db_session.query(cls).filter(cls.series_code == series_code).first()
        if existing:
            existing.part_count += 1
            return existing
        
        new_series = cls(series_code=series_code, part_count=1)
        db_session.add(new_series)
        db_session.flush()
        return new_series
