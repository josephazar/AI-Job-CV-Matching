from pydantic import BaseModel, Field


class Position(BaseModel):
    qualifications: str
    recruitment_id: str
    name: str


class JobConfidence(BaseModel):
    pdf: list[str] = Field(default_factory=list)
    positions: list[Position] = Field(default_factory=list)
