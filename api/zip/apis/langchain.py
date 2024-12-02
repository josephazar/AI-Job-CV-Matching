from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from langchain_openai import AzureChatOpenAI
import os
import re
model1=AzureChatOpenAI(openai_api_version=os.environ.get("OPENAI_CHAT_API_VERSION"),azure_deployment=os.environ.get("OPENAI_CHAT_MODEL_NAME"),api_key=os.environ.get("OPENAI_CHAT_API_KEY"),azure_endpoint=os.environ.get("OPENAI_CHAT_API_BASE"))



class WorkExperienceItem(BaseModel):
    job_title: Optional[str] = Field("Not Mentionned", description="The title of the job position")
    company: Optional[str] = Field("Not Mentionned", description="The name of the company without writing the country")
    start_month:Optional[str]=Field(...,description="the start month of the job using this format MM")
    start_year:Optional[str] = Field(..., description="The start year of the job using this format YYYY")
    end_year:Optional[str] = Field(..., description="The end year of the job using this format: YYYY")
    end_month:Optional[str]=Field(...,description="the end month of the job using this format MM")
    @validator('start_year','start_month', 'end_year', 'end_month', pre=True, always=True)
    def replace_none(cls, v):
        return v or "Not Mentioned"
    
    
class categoryWork(BaseModel):
    # category:str=Field(...,description="name of the category")
    items:List[WorkExperienceItem]=Field(...,description="list of work experience items")
    confidence: int = Field(..., description="Confidence level in the accuracy of the extracted information")
    
class EducationItem(BaseModel):
    major: Optional[str] = Field("Not Mentionned", description="Major field of study")
    degree_type: Optional[str] = Field("Not Mentionned", description="Type of degree obtained")
    institution: Optional[str] = Field("Not Mentionned", description="The institution from which the degree was obtained without writing the country")
    start_month:Optional[str]=Field(...,description="the start month of the degree program")
    start_year:Optional[str] = Field(..., description="The start year of the degree program")
    end_year:Optional[str] = Field(..., description="The end year of the degree program")
    end_month:Optional[str]=Field(...,description="the end month of the degree program")
    @validator('start_year','start_month', 'end_year', 'end_month', pre=True, always=True)
    def replace_none(cls, v):
        return v or "Not Mentioned"

class categoryEducation(BaseModel):
    # category:str=Field(...,description="name of the category")
    items:List[EducationItem]=Field(None,description="list of education items")

class Skill(BaseModel):
    skills: Optional[str] = Field("Not Mentionned", description="Description of the skill")
    
    

class categorySkill(BaseModel):
    # category:str="Skills"
    items:List[str] = Field("Not Mentionned", description="List of skills as strings")
    confidence: int = Field(..., description="Confidence level in the accuracy of the extracted information")

class Certification(BaseModel):
    items:List[str] = Field("Not Mentionned", description="List of certifications")
    confidence: int = Field(..., description="Confidence level in the accuracy of the extracted information")

class Language(BaseModel):
    language:  Optional[str]  = Field("Not Mentionned", description="The language")
    proficiency:  Optional[str]  = Field("Not Mentionned", description="Proficiency level in the language")
    # confidence: int = Field(..., description="Confidence level in the accuracy of the extracted information")

class categoryLanguage(BaseModel):
    # category:str="Languages"
    items:List[Language]=Field("Not Mentionned",description="List of Languages")
    confidence: int = Field(..., description="Confidence level in the accuracy of the extracted information")
    
class PersonnelInfoItem(BaseModel):
    first_name:  str  = Field(..., description="First name of the individual")
    last_name:  str  = Field(..., description="Last name of the individual")
    address: Optional[str] = Field("Not Mentionned", description="Address of the individual")
    phone_number:  Optional[str]  = Field("Not Mentionned", description="Phone number of the individual")
    email:  Optional[str]  = Field("Not Mentionned", description="Email address of the individual")
    confidence: int = Field(90, description="Confidence level in the accuracy of the extracted information")
    @validator( 'address', 'phone_number','email', pre=True, always=True)
    def replace_none(cls, v):
        return v or "Not Mentioned"
    



class Resume(BaseModel):
    # category:str="resume"
    Work_Experience: categoryWork = Field(..., description="List of work experience items")
    Education: categoryEducation = Field(..., description="List of education items")
    Skills: categorySkill = Field(..., description="List of skills")
    Certifications: Certification= Field(..., description="List of certifications")
    Languages: categoryLanguage = Field(..., description="List of languages spoken")
    Personnel_info: PersonnelInfoItem = Field(..., description="Personal information of the individual")

parser = PydanticOutputParser(pydantic_object=Resume)
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)


def resume_parser(resume):
    human_prompt=HumanMessagePromptTemplate.from_template("{request}\n {format_instructions}")
    chat_prompt=ChatPromptTemplate.from_messages([human_prompt])
    resume = re.sub(r"[^\w\s()+.@-]", "", resume)
    print("///////////////cleaned resume")
    print(resume)
    print("///////////////cleaned resume")
    request=chat_prompt.format_prompt(request=f"i have this resume {resume}",
    format_instructions=parser.get_format_instructions()).to_messages()
    # print(request)
    
    result=model1.invoke(request,temperature=0)
    print("////////////// before parsing")
    print(result.content)
    print("////////////// before parsing")
    parsed_resume=parser.parse(result.content)
    print("///////////////parsed resume")
    print(parsed_resume)
    print("///////////////parsed resume")
    
    
    return parsed_resume

def replace_none_with_not_mentioned(value):
    if isinstance(value, dict):
        for key, val in value.items():
            value[key] = replace_none_with_not_mentioned(val)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            value[i] = replace_none_with_not_mentioned(item)
    elif value is None or value == "null":
        return "Not Mentioned"
    return value