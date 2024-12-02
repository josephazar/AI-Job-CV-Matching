from fastapi import APIRouter, Request

from apis.apis import get_job_offer
from models.JobDescription import JobDescription

main_route = APIRouter()

@main_route.get("/")
async def home():
    return {"message": "Hello from HREX AI"}


