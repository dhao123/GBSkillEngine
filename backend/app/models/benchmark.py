"""
GBSkillEngine Benchmark 评测系统数据模型

包含:
- BenchmarkDataset: 评测数据集
- BenchmarkCase: 测试用例
- BenchmarkRun: 评测运行记录
- BenchmarkResult: 评测结果
- GenerationTemplate: 数据生成模板
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class DatasetSourceType(str, enum.Enum):
    """数据集来源类型"""
    SEED = "seed"           # 人工标注的种子数据
    GENERATED = "generated" # 自动生成的数据
    MIXED = "mixed"         # 混合数据


class DatasetStatus(str, enum.Enum):
    """数据集状态"""
    DRAFT = "draft"       # 草稿
    READY = "ready"       # 就绪可用
    ARCHIVED = "archived" # 已归档


class CaseDifficulty(str, enum.Enum):
    """用例难度等级"""
    EASY = "easy"               # 简单: 标准格式、完整信息
    MEDIUM = "medium"           # 中等: 部分省略、非标写法
    HARD = "hard"               # 困难: 需要推理、缺少关键信息
    ADVERSARIAL = "adversarial" # 对抗: 干扰信息、边界情况


class CaseSourceType(str, enum.Enum):
    """用例来源类型"""
    SEED = "seed"             # 人工标注
    TABLE_ENUM = "table_enum" # 表格枚举
    TEMPLATE = "template"     # 模板生成
    NOISE = "noise"           # 噪声注入


class RunStatus(str, enum.Enum):
    """评测运行状态"""
    PENDING = "pending"     # 等待中
    RUNNING = "running"     # 运行中
    COMPLETED = "completed" # 已完成
    FAILED = "failed"       # 失败


class ResultStatus(str, enum.Enum):
    """评测结果状态"""
    SUCCESS = "success"   # 成功(完全匹配)
    PARTIAL = "partial"   # 部分匹配
    FAILED = "failed"     # 失败(不匹配)
    ERROR = "error"       # 执行错误


class BenchmarkDataset(Base):
    """Benchmark评测数据集"""
    __tablename__ = "benchmark_datasets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_code = Column(String(100), unique=True, nullable=False, index=True, comment="数据集唯一编码")
    dataset_name = Column(String(500), nullable=False, comment="数据集名称")
    description = Column(Text, nullable=True, comment="描述")
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, comment="关联的Skill ID")
    source_type = Column(String(50), nullable=False, default=DatasetSourceType.MIXED.value, comment="来源类型")
    difficulty_distribution = Column(JSON, nullable=True, comment="难度分布")
    total_cases = Column(Integer, nullable=False, default=0, comment="总用例数")
    status = Column(String(50), nullable=False, default=DatasetStatus.DRAFT.value, comment="状态")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    # 关系
    skill = relationship("Skill", backref="benchmark_datasets")
    cases = relationship("BenchmarkCase", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("BenchmarkRun", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BenchmarkDataset {self.dataset_code}: {self.dataset_name}>"
    
    def update_case_count(self):
        """更新用例数量"""
        self.total_cases = len([c for c in self.cases if c.is_active])
    
    def get_difficulty_stats(self) -> dict:
        """获取难度分布统计"""
        stats = {d.value: 0 for d in CaseDifficulty}
        for case in self.cases:
            if case.is_active and case.difficulty in stats:
                stats[case.difficulty] += 1
        return stats


class BenchmarkCase(Base):
    """Benchmark测试用例"""
    __tablename__ = "benchmark_cases"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("benchmark_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    case_code = Column(String(100), nullable=False, index=True, comment="用例编码")
    input_text = Column(Text, nullable=False, comment="输入文本(物料描述)")
    expected_skill_id = Column(String(200), nullable=True, comment="期望匹配的Skill ID")
    expected_attributes = Column(JSON, nullable=False, comment="期望输出属性")
    expected_category = Column(JSON, nullable=True, comment="期望类目映射")
    difficulty = Column(String(50), nullable=False, default=CaseDifficulty.MEDIUM.value, index=True, comment="难度")
    source_type = Column(String(50), nullable=False, default=CaseSourceType.SEED.value, comment="来源类型")
    source_reference = Column(JSON, nullable=True, comment="来源追溯")
    tags = Column(JSON, nullable=True, comment="标签数组")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    dataset = relationship("BenchmarkDataset", back_populates="cases")
    results = relationship("BenchmarkResult", back_populates="case", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BenchmarkCase {self.case_code}: {self.input_text[:50]}...>"


class BenchmarkRun(Base):
    """Benchmark评测运行记录"""
    __tablename__ = "benchmark_runs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_code = Column(String(100), unique=True, nullable=False, index=True, comment="评测运行编码")
    dataset_id = Column(Integer, ForeignKey("benchmark_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    run_name = Column(String(500), nullable=True, comment="运行名称")
    description = Column(Text, nullable=True, comment="描述")
    config = Column(JSON, nullable=True, comment="运行配置")
    status = Column(String(50), nullable=False, default=RunStatus.PENDING.value, index=True, comment="状态")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    total_cases = Column(Integer, nullable=False, default=0, comment="总用例数")
    completed_cases = Column(Integer, nullable=False, default=0, comment="已完成用例数")
    metrics = Column(JSON, nullable=True, comment="汇总指标")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    # 关系
    dataset = relationship("BenchmarkDataset", back_populates="runs")
    results = relationship("BenchmarkResult", back_populates="run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BenchmarkRun {self.run_code}: {self.status}>"
    
    @property
    def progress(self) -> float:
        """计算进度百分比"""
        if self.total_cases == 0:
            return 0.0
        return round(self.completed_cases / self.total_cases * 100, 2)


class BenchmarkResult(Base):
    """Benchmark评测结果"""
    __tablename__ = "benchmark_results"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("benchmark_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("benchmark_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    actual_skill_id = Column(String(200), nullable=True, comment="实际匹配的Skill ID")
    actual_attributes = Column(JSON, nullable=True, comment="实际输出属性")
    actual_category = Column(JSON, nullable=True, comment="实际类目")
    actual_confidence = Column(Float, nullable=True, comment="实际置信度")
    execution_time_ms = Column(Integer, nullable=True, comment="执行耗时(毫秒)")
    skill_match = Column(Boolean, nullable=True, comment="Skill是否匹配")
    attribute_scores = Column(JSON, nullable=True, comment="各属性评分")
    overall_score = Column(Float, nullable=True, comment="综合得分 0-1")
    status = Column(String(50), nullable=False, default=ResultStatus.SUCCESS.value, index=True, comment="状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    run = relationship("BenchmarkRun", back_populates="results")
    case = relationship("BenchmarkCase", back_populates="results")
    
    def __repr__(self):
        return f"<BenchmarkResult run={self.run_id} case={self.case_id}: {self.status}>"


class GenerationTemplate(Base):
    """数据生成模板"""
    __tablename__ = "generation_templates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_code = Column(String(100), unique=True, nullable=False, index=True, comment="模板编码")
    template_name = Column(String(200), nullable=False, comment="模板名称")
    domain = Column(String(100), nullable=True, index=True, comment="适用领域")
    pattern = Column(Text, nullable=False, comment="模板模式")
    variants = Column(JSON, nullable=True, comment="变体列表")
    noise_rules = Column(JSON, nullable=True, comment="噪声规则")
    difficulty_weight = Column(String(50), nullable=True, comment="生成难度倾向")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<GenerationTemplate {self.template_code}: {self.template_name}>"
