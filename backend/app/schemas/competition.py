import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CompetitionPlatform, CompetitionStatus
from app.schemas.file import CompetitionFileRead


class CompetitionBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Competition title")
    platform: str = Field(default=CompetitionPlatform.ZINDI.value, description="Host platform (zindi, kaggle, custom)")
    description: Optional[str] = Field(default=None, description="Problem statement or overview description")
    config_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom user configuration")


class CompetitionCreate(CompetitionBase):
    slug: Optional[str] = None

    @model_validator(mode="after")
    def populate_slug_if_empty(self) -> "CompetitionCreate":
        if not self.slug:
            clean = re.sub(r"[^\w\s-]", "", self.title.lower()).strip()
            self.slug = re.sub(r"[-\s]+", "-", clean)
        return self


class CompetitionUpdate(BaseModel):
    title: Optional[str] = None
    platform: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    config_overrides: Optional[Dict[str, Any]] = None


class CompetitionRead(CompetitionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime


class CompetitionDetail(CompetitionRead):
    files: List[CompetitionFileRead] = []
