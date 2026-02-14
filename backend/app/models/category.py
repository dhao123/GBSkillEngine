"""
GBSkillEngine 类目(Category)模型

Category是4级树状结构，从国标文件的产品范围中提取：
- Level 1: 领域（对应Domain）
- Level 2: 产品大类
- Level 3: 具体产品
- Level 4: 规格/型号分类
"""
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    """
    类目表 - 4级产品分类树
    
    通过自引用 parent_id 实现树状结构。
    level字段标识所属层级（1-4）。
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_code = Column(String(100), unique=True, nullable=False, index=True,
                          comment="类目编码，如 pipe.seamless.carbon")
    category_name = Column(String(200), nullable=False,
                          comment="类目名称，如 碳素钢无缝钢管")
    level = Column(Integer, nullable=False, index=True,
                  comment="层级：1=领域, 2=产品大类, 3=具体产品, 4=规格")
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True,
                      comment="父类目ID，顶级类目为NULL")
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True,
                      comment="所属领域ID")
    full_path = Column(String(500), nullable=True,
                      comment="完整路径，如 管材管件/无缝钢管/碳素钢无缝钢管")
    description = Column(Text, nullable=True,
                        comment="类目描述")
    standard_count = Column(Integer, default=0,
                           comment="该类目关联的国标数量")
    skill_count = Column(Integer, default=0,
                        comment="该类目关联的Skill数量")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                       comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), comment="更新时间")
    
    # 自引用关系
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    
    # 其他关系
    domain = relationship("Domain", back_populates="categories")
    standards = relationship("Standard", back_populates="category")
    skills = relationship("Skill", back_populates="category")
    
    def __repr__(self):
        return f"<Category L{self.level} {self.category_code}: {self.category_name}>"
    
    @property
    def is_leaf(self) -> bool:
        """是否为叶子节点"""
        return self.level == 4 or len(self.children) == 0
    
    def get_ancestors(self) -> List["Category"]:
        """获取所有祖先节点（从根到父）"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_descendants(self, db_session) -> List["Category"]:
        """获取所有后代节点"""
        descendants = []
        children = db_session.query(Category).filter(Category.parent_id == self.id).all()
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_descendants(db_session))
        return descendants
    
    def build_full_path(self) -> str:
        """构建完整路径"""
        ancestors = self.get_ancestors()
        names = [a.category_name for a in ancestors] + [self.category_name]
        return "/".join(names)
    
    @classmethod
    def get_or_create(cls, db_session, category_code: str, category_name: str,
                      level: int, parent_id: Optional[int] = None,
                      domain_id: Optional[int] = None) -> "Category":
        """
        获取或创建类目
        
        Args:
            db_session: 数据库会话
            category_code: 类目编码
            category_name: 类目名称
            level: 层级（1-4）
            parent_id: 父类目ID
            domain_id: 领域ID
            
        Returns:
            Category: 类目对象
        """
        existing = db_session.query(cls).filter(cls.category_code == category_code).first()
        if existing:
            return existing
        
        new_category = cls(
            category_code=category_code,
            category_name=category_name,
            level=level,
            parent_id=parent_id,
            domain_id=domain_id
        )
        db_session.add(new_category)
        db_session.flush()
        
        # 构建完整路径
        new_category.full_path = new_category.build_full_path()
        db_session.flush()
        
        return new_category
    
    @classmethod
    def create_hierarchy_from_list(cls, db_session, category_list: List[str],
                                   domain_id: int) -> "Category":
        """
        从类目名称列表创建层级结构
        
        Args:
            db_session: 数据库会话
            category_list: 类目名称列表，按层级排列
                          如 ["管材管件", "无缝钢管", "碳素钢无缝钢管", "DN100"]
            domain_id: 领域ID
            
        Returns:
            Category: 最末级（最具体）的类目对象
        """
        parent_id = None
        last_category = None
        code_parts = []
        
        for i, name in enumerate(category_list[:4]):  # 最多4级
            level = i + 1
            code_parts.append(name.replace(" ", "_").lower())
            category_code = ".".join(code_parts)
            
            last_category = cls.get_or_create(
                db_session=db_session,
                category_code=category_code,
                category_name=name,
                level=level,
                parent_id=parent_id,
                domain_id=domain_id if level == 1 else None
            )
            parent_id = last_category.id
        
        return last_category
