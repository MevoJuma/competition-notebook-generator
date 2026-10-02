from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int = 0
    unique_count: Optional[int] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None


class DatasetProfileCreate(BaseModel):
    competition_id: str
    file_id: Optional[str] = None
    dataset_name: str
    role: str = "unknown"
    row_count: int
    column_count: int
    memory_bytes: int
    schema_definition: Dict[str, str]
    column_profiles: Dict[str, ColumnProfile]
    sample_rows: List[Dict[str, Any]]


class DatasetProfileResponse(DatasetProfileCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)
