from fastapi import APIRouter, Request

from apis.apis import get_job_offer,get_job_offer_chat
from models.JobDescription import JobDescription
import os
job_route = APIRouter(prefix="/job/v1", tags=["Job"])
GPT_TYPE=os.environ.get("GPT_TYPE")

@job_route.post("/generate_description")
async def generate_description(request: Request, data: JobDescription):
    if(GPT_TYPE=="completion"):
        return get_job_offer(data)
    elif(GPT_TYPE=="chat"):
        return get_job_offer_chat(data)
 