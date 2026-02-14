"""
GBSkillEngine Benchmark 评测系统 Pydantic Schemas

定义API请求和响应的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============= 枚举类型 =============

class DatasetSourceType(str, Enum):
    """数据集来源类型"""
    SEED = "seed"
    GENERATED = "generated"
    MIXED = "mixed"


class DatasetStatus(str, Enum):
    """数据集状态"""
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class CaseDifficulty(str, Enum):
    """用例难度等级"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADVERSARIAL = "adversarial"


class CaseSourceType(str, Enum):
    """用例来源类型"""
    SEED = "seed"
    TABLE_ENUM = "table_enum"
    TEMPLATE = "template"
    NOISE = "noise"


class RunStatus(str, Enum):
    """评测运行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultStatus(str, Enum):
    """评测结果状态"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ERROR = "error"


# ============= 期望属性结构 =============

class ExpectedAttribute(BaseModel):
    """期望属性值"""
    value: Any = Field(..., description="属性值")
    unit: str = Field("", description="单位")
    tolerance: Optional[float] = Field(None, description="容差范围")


# ============= 数据集 Schemas =============

class BenchmarkDatasetBase(BaseModel):
    """数据集基础字段"""
    dataset_code: str = Field(..., min_length=1, max_length=100, description="数据集唯一编码")
    dataset_name: str = Field(..., min_length=1, max_length=500, description="数据集名称")
    description: Optional[str] = Field(None, description="描述")
    skill_id: Optional[int] = Field(None, description="关联的Skill ID")
    source_type: DatasetSourceType = Field(DatasetSourceType.MIXED, description="来源类型")


class BenchmarkDatasetCreate(BenchmarkDatasetBase):
    """创建数据集"""
    pass


class BenchmarkDatasetUpdate(BaseModel):
    """更新数据集"""
    dataset_name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    skill_id: Optional[int] = None
    source_type: Optional[DatasetSourceType] = None
    status: Optional[DatasetStatus] = None


class BenchmarkDatasetResponse(BenchmarkDatasetBase):
    """数据集响应"""
    id: int
    status: DatasetStatus
    total_cases: int
    difficulty_distribution: Optional[Dict[str, int]] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class BenchmarkDatasetListResponse(BaseModel):
    """数据集列表响应"""
    total: int
    items: List[BenchmarkDatasetResponse]


# ============= 测试用例 Schemas =============

class BenchmarkCaseBase(BaseModel):
    """测试用例基础字段"""
    input_text: str = Field(..., min_length=1, description="输入文本(物料描述)")
    expected_skill_id: Optional[str] = Field(None, description="期望匹配的Skill ID")
    expected_attributes: Dict[str, ExpectedAttribute] = Field(..., description="期望输出属性")
    expected_category: Optional[Dict[str, str]] = Field(None, description="期望类目映射")
    difficulty: CaseDifficulty = Field(CaseDifficulty.MEDIUM, description="难度")
    source_type: CaseSourceType = Field(CaseSourceType.SEED, description="来源类型")
    source_reference: Optional[Dict[str, Any]] = Field(None, description="来源追溯")
    tags: Optional[List[str]] = Field(None, description="标签")


class BenchmarkCaseCreate(BenchmarkCaseBase):
    """创建测试用例"""
    case_code: Optional[str] = Field(None, description="用例编码，不提供则自动生成")


class BenchmarkCaseUpdate(BaseModel):
    """更新测试用例"""
    input_text: Optional[str] = None
    expected_skill_id: Optional[str] = None
    expected_attributes: Optional[Dict[str, ExpectedAttribute]] = None
    expected_category: Optional[Dict[str, str]] = None
    difficulty: Optional[CaseDifficulty] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class BenchmarkCaseResponse(BenchmarkCaseBase):
    """测试用例响应"""
    id: int
    dataset_id: int
    case_code: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class BenchmarkCaseListResponse(BaseModel):
    """测试用例列表响应"""
    total: int
    items: List[BenchmarkCaseResponse]


class BenchmarkCaseBatchCreate(BaseModel):
    """批量创建测试用例"""
    cases: List[BenchmarkCaseCreate] = Field(..., min_length=1, description="用例列表")


# ============= 数据生成 Schemas =============

class GenerationOptions(BaseModel):
    """数据生成选项"""
    skill_id: int = Field(..., description="目标Skill ID")
    count: int = Field(100, ge=1, le=10000, description="生成数量")
    difficulty_distribution: Optional[Dict[str, int]] = Field(
        None,
        description="难度分布百分比，如 {'easy': 40, 'medium': 30, 'hard': 20, 'adversarial': 10}"
    )
    include_noise: bool = Field(True, description="是否包含噪声变体")
    include_variants: bool = Field(True, description="是否包含模板变体")
    template_ids: Optional[List[int]] = Field(None, description="指定使用的模板ID列表")


class GenerationResult(BaseModel):
    """数据生成结果"""
    generated_count: int = Field(..., description="成功生成数量")
    cases: List[BenchmarkCaseResponse] = Field(..., description="生成的用例")
    stats: Dict[str, Any] = Field(..., description="生成统计信息")


# ============= 评测运行 Schemas =============

class EvaluationConfig(BaseModel):
    """评测配置"""
    tolerance: float = Field(0.05, ge=0, le=1, description="数值属性容差比例")
    partial_match: bool = Field(True, description="是否计算部分匹配分数")
    skip_skill_match: bool = Field(False, description="跳过Skill匹配检查")


class BenchmarkRunCreate(BaseModel):
    """创建评测运行"""
    dataset_id: int = Field(..., description="数据集ID")
    run_name: Optional[str] = Field(None, description="运行名称")
    description: Optional[str] = Field(None, description="描述")
    config: Optional[EvaluationConfig] = Field(None, description="评测配置")


class BenchmarkRunResponse(BaseModel):
    """评测运行响应"""
    id: int
    run_code: str
    dataset_id: int
    run_name: Optional[str]
    description: Optional[str]
    config: Optional[Dict[str, Any]]
    status: RunStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_cases: int
    completed_cases: int
    progress: float = Field(..., description="进度百分比")
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class BenchmarkRunListResponse(BaseModel):
    """评测运行列表响应"""
    total: int
    items: List[BenchmarkRunResponse]


# ============= 评测结果 Schemas =============

class AttributeScore(BaseModel):
    """单个属性评分"""
    expected: Any = Field(..., description="期望值")
    actual: Any = Field(None, description="实际值")
    match: bool = Field(..., description="是否匹配")
    score: float = Field(..., ge=0, le=1, description="得分")
    match_type: str = Field("exact", description="匹配类型: exact/tolerance/fuzzy/missing")


class BenchmarkResultResponse(BaseModel):
    """评测结果响应"""
    id: int
    run_id: int
    case_id: int
    actual_skill_id: Optional[str]
    actual_attributes: Optional[Dict[str, Any]]
    actual_category: Optional[Dict[str, str]]
    actual_confidence: Optional[float]
    execution_time_ms: Optional[int]
    skill_match: Optional[bool]
    attribute_scores: Optional[Dict[str, AttributeScore]]
    overall_score: Optional[float]
    status: ResultStatus
    error_message: Optional[str]
    created_at: datetime
    
    # 关联的用例信息
    case_code: Optional[str] = None
    input_text: Optional[str] = None
    difficulty: Optional[str] = None
    
    class Config:
        from_attributes = True


class BenchmarkResultListResponse(BaseModel):
    """评测结果列表响应"""
    total: int
    items: List[BenchmarkResultResponse]


# ============= 评测指标 Schemas =============

class DifficultyMetrics(BaseModel):
    """按难度级别的指标"""
    count: int = Field(..., description="用例数量")
    accuracy: float = Field(..., description="准确率")
    avg_score: float = Field(..., description="平均得分")


class AttributeMetrics(BaseModel):
    """属性级别指标"""
    total: int = Field(..., description="总数")
    exact_match: float = Field(..., description="精确匹配率")
    within_tolerance: float = Field(..., description="容差匹配率")
    missing_rate: float = Field(..., description="缺失率")


class OverallMetrics(BaseModel):
    """总体指标"""
    total_cases: int = Field(..., description="总用例数")
    accuracy: float = Field(..., description="准确率(完全匹配)")
    partial_accuracy: float = Field(..., description="部分准确率")
    skill_match_rate: float = Field(..., description="Skill匹配率")
    avg_confidence: float = Field(..., description="平均置信度")
    avg_score: float = Field(..., description="平均得分")
    avg_execution_time_ms: float = Field(..., description="平均执行时间")


class BenchmarkMetrics(BaseModel):
    """评测指标汇总"""
    overall: OverallMetrics = Field(..., description="总体指标")
    by_difficulty: Dict[str, DifficultyMetrics] = Field(..., description="按难度的指标")
    by_attribute: Dict[str, AttributeMetrics] = Field(..., description="按属性的指标")
    by_status: Dict[str, int] = Field(..., description="按状态的分布")


# ============= 生成模板 Schemas =============

class GenerationTemplateBase(BaseModel):
    """生成模板基础字段"""
    template_code: str = Field(..., min_length=1, max_length=100, description="模板编码")
    template_name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    domain: Optional[str] = Field(None, max_length=100, description="适用领域")
    pattern: str = Field(..., description="模板模式")
    variants: Optional[List[str]] = Field(None, description="变体列表")
    noise_rules: Optional[Dict[str, Any]] = Field(None, description="噪声规则")
    difficulty_weight: Optional[str] = Field(None, description="生成难度倾向")


class GenerationTemplateCreate(GenerationTemplateBase):
    """创建生成模板"""
    pass


class GenerationTemplateUpdate(BaseModel):
    """更新生成模板"""
    template_name: Optional[str] = None
    domain: Optional[str] = None
    pattern: Optional[str] = None
    variants: Optional[List[str]] = None
    noise_rules: Optional[Dict[str, Any]] = None
    difficulty_weight: Optional[str] = None
    is_active: Optional[bool] = None


class GenerationTemplateResponse(GenerationTemplateBase):
    """生成模板响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GenerationTemplateListResponse(BaseModel):
    """生成模板列表响应"""
    total: int
    items: List[GenerationTemplateResponse]


class TemplatePreviewRequest(BaseModel):
    """模板预览请求"""
    count: int = Field(5, ge=1, le=20, description="预览数量")
    attributes: Optional[Dict[str, Any]] = Field(None, description="自定义属性值")


class TemplatePreviewResponse(BaseModel):
    """模板预览响应"""
    samples: List[str] = Field(..., description="生成的样例文本")
