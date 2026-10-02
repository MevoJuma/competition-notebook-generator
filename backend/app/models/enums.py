import enum


class CompetitionPlatform(str, enum.Enum):
    ZINDI = "zindi"
    KAGGLE = "kaggle"
    CUSTOM = "custom"


class CompetitionStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    EXPERIMENTING = "EXPERIMENTING"
    EXPERIMENT_COMPLETED = "EXPERIMENT_COMPLETED"
    GENERATING_NOTEBOOK = "GENERATING_NOTEBOOK"
    VALIDATING_NOTEBOOK = "VALIDATING_NOTEBOOK"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FileCategory(str, enum.Enum):
    TRAIN_DATA = "TRAIN_DATA"
    TEST_DATA = "TEST_DATA"
    SAMPLE_SUBMISSION = "SAMPLE_SUBMISSION"
    METADATA_DICTIONARY = "METADATA_DICTIONARY"
    DOCUMENTATION_RULES = "DOCUMENTATION_RULES"
    SUPPLEMENTARY_DATA = "SUPPLEMENTARY_DATA"
    UNKNOWN = "UNKNOWN"


class ProblemType(str, enum.Enum):
    BINARY_CLASSIFICATION = "Binary Classification"
    MULTICLASS_CLASSIFICATION = "Multiclass Classification"
    MULTILABEL_CLASSIFICATION = "Multilabel Classification"
    REGRESSION = "Regression"
    TIME_SERIES_FORECASTING = "Time-Series Forecasting"
    RANKING = "Ranking"
    RECOMMENDER = "Recommender Systems"
    NLP = "Natural Language Processing"
    COMPUTER_VISION = "Computer Vision"
    OTHER = "Other"


class MetricDirection(str, enum.Enum):
    MAXIMIZE = "MAXIMIZE"
    MINIMIZE = "MINIMIZE"


class ValidationStrategyType(str, enum.Enum):
    STRATIFIED_K_FOLD = "StratifiedKFold"
    K_FOLD = "KFold"
    GROUP_K_FOLD = "GroupKFold"
    STRATIFIED_GROUP_K_FOLD = "StratifiedGroupKFold"
    TIME_SERIES_SPLIT = "TimeSeriesSplit"
    HOLDOUT = "Holdout"


class NotebookStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
