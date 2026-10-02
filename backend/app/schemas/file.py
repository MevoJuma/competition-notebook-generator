from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class CompetitionFileBase(BaseModel):
    filename: str
    original_name: str
    file_type: str
    category: str
    file_size_bytes: int
    file_hash: str


class CompetitionFileCreate(CompetitionFileBase):
    competition_id: str
    storage_path: str
    metadata_json: Optional[Dict[str, Any]] = None


class CompetitionFileUpdate(BaseModel):
    category: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class CompetitionFileRead(CompetitionFileBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    competition_id: str
    storage_path: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
