import concurrent.futures

from fastapi import APIRouter, Request

from apis.functions import ner_stream, ner_stream_confidence, ner_job_confidence,ner_job_confidence_chat,ner_job_confidence_chat_llm
# from apis.langchain import resume_parser
from models.JobConfidence import JobConfidence
import os
resume_route = APIRouter(prefix="/resume/v1", tags=["Resume"])


# @resume_route.post("/ner-stream")
# async def ner_stream_route(request: Request):
#     if 'Content-Type' in request.headers and request.headers['Content-Type'] == 'application/octet-stream':
#         return ner_stream(request.body())
#
#
# @resume_route.post("/ner-stream-confidence")
# async def ner_stream_confidence_route(request: Request):
#     if 'Content-Type' in request.headers and request.headers['Content-Type'] == 'application/octet-stream':
#         return ner_stream_confidence(request.body())

GPT_TYPE=os.environ.get("GPT_TYPE")
@resume_route.post('/ner-job-confidence')
async def ner_job_confidence_route(request: Request, data: JobConfidence):
        if(GPT_TYPE=="completion"):
                return await ner_job_confidence(**data.__dict__)
        elif(GPT_TYPE=="chat"):
                return await ner_job_confidence_chat(**data.__dict__)

@resume_route.post('/ner-job-confidence-new')
async def ner_job_confidence_route(request: Request, data: JobConfidence):


        return await ner_job_confidence_chat_llm(**data.__dict__)

#http://localhost:7071/resume/v1/ner-job-confidence