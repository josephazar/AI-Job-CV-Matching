import json
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class UnAuthorizatedRequest(BaseModel):
    result: Annotated[str, Query(default="error")]
    errors: list | None
    message:  Annotated[str, Query(default="Something went wrong!")]
