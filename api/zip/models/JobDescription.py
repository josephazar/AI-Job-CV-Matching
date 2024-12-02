from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    job_title: str = Field(max_length=60)
    experience: int = Field(default=1)
    degree:str = Field(max_length=150)
    job_description: str = Field(max_length=300)
    writing_tone: str = Field(max_length=30, default="professional")
    language: str = Field(max_length=30, default="english")
    company:  str = Field(max_length=60)
    # country:  str = Field(max_length=100)
    # currency: str = Field(min_length=3, max_length=4)
