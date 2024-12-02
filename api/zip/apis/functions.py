import asyncio
import json
import os
import re
import concurrent.futures
import time
from concurrent.futures import wait, ALL_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor

from langchain.agents import load_tools, initialize_agent
# from langchain.document_loaders import pdf
# from langchain.llms import AzureOpenAI

from apis.openai import get_openai as openai
from apis.openai import get_openai_chat as openai_chat

from apis.langchain import resume_parser

from models.JobConfidence import JobConfidence, Position
from prompts.main import extract_salary_range, cv_review_prompt_confidence, cv_job_review_prompt_confidence, \
    cv_review_prompt
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import base64


tokens = 3000
small_token=500
# from apis.openai import get_openai as openai
endpoint = os.environ.get("FORM_RECOGNIZER_ENDPOINT")
key = os.environ.get("FORM_RECOGNIZER_KEY")
model_name=os.environ.get("OPENAI_CHAT_MODEL_NAME")

# def langchainAgent(inputText):
#     print("input")
#     print(inputText)
#     print("input")
#     tools = load_tools(["bing-search"])
#     llm = AzureOpenAI(openai_api_version=openai().api_version, azure_deployment="ex-turbo-instruct",
#                       api_key=openai().api_key, base_url=openai().api_base)
#     agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=False)
#     salaryResponse = agent.run(inputText)

#     print("salary resposen")
#     print(salaryResponse)
#     print("salary response")
#     return salaryResponse


def salaryRange(salaryResponse):
    prompt = extract_salary_range.format(minmaxsalary=salaryResponse)
    print("prompt")
    print(prompt)
    print("prmpt")
    response = openai().Completion.create(
        engine="ex-turbo-instruct",
        prompt=prompt,
        temperature=0.1,
        max_tokens=tokens,
        top_p=0.1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
    response_text = response["choices"][0]["text"]
    response_text = response_text.replace("\n", "")
    salary_json = json.loads(response_text)
    return salary_json



def split(input_string):
    print(input_string)
    sections = re.split(r'\n\n(?=\w+:)', input_string)
    # sections = re.split(r'\n(?=\w+:)', input_string)
    keys = ["Title", "Description", "Information", "Responsibilities", "Requirements", "Certifications", "Remaining"]
    section_dict = {}

    sections = re.split(r'\n(?=\w+:)', input_string)

    section_dict = {}

    for section in sections:
        section = section.strip()

        if section.startswith("Title:"):
            section_dict["Title"] = section.replace("Title:", "").strip()
        elif section.startswith("Description:"):
            section_dict["Description"] = section.replace("Description:", "").strip()
        elif section.startswith("Information:") or section.startswith("Company Information:"):
            section_dict["Information"] = section.replace("Information:", "").strip()
        elif section.startswith("Responsibilities:"):
            section_dict["Responsibilities"] = section.replace("Responsibilities:", "").strip()
        elif section.startswith("Requirements:"):
            section_dict["Requirements"] = section.replace("Requirements:", "").strip()
        elif section.startswith("Certifications:"):
            section_dict["Certifications"] = section.replace("Certifications:", "").strip()
        elif section.startswith("Remaining"):
            section_dict["Remaining"] = section.replace("Remaining:", "").strip()
        else:
            section_dict["Text"] = section.strip()

    return section_dict


def analyze_read(base64_data):
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    bytes_data = base64.b64decode(base64_data)
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-layout", document=bytes_data
    )
    result = poller.result()
    print("OCR////////////////////////////")
    print(result.content)
    print("OCR////////////////////////////")
    return result.content


def create_json_response(response_text):
    # print("///////////////////////////////// resume")
    # print(response_text)
    # print("///////////////////////////////// resume")
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]

    response_data = {"data": []}
    current_category = None
    items = []
    confidence = None

    for line in lines:
        if line.startswith('-') and not (
                line.lower().startswith('- confidence:') or line.lower().startswith('-confidence') or line.lower().startswith('confidence')):
            items.append(line.strip('- ').strip())
        elif line.lower().startswith('- confidence:') or line.lower().startswith('-confidence') or line.lower().startswith('confidence'):
            confidence = int(line.split(':')[1].strip().strip('%'))
        else:
            if current_category is not None:
                response_data["data"].append({
                    "category": current_category,
                    "items": items,
                    "confidence": confidence
                })
            current_category = line.rstrip(':')
            items = []
            # confidence = None

    if current_category is not None:
        response_data["data"].append({
            "category": current_category,
            "items": items,
            "confidence": confidence
        })
    response_data = edit_response(response_data)
    json_response = json.dumps(response_data, indent=2)
    return json_response


def edit_response(response_data):
    print("edit response")
    print(response_data)
    print("edit response")
    for item in response_data.items():
        for arr_items in item[1]:
            print(arr_items['category'])
            if arr_items['category'] == 'Education':
                temp = []
                for i in arr_items['items']:
                    if (len(i.split(", ")) == 4):
                        components = i.split(", ")
                        result = f"{components[0]}, {components[1]}, {components[2]}, {process_date(components[3])}"
                        temp.append(result)
                arr_items['items'] = temp
                print(arr_items['items'])
                if len(arr_items['items']) == 0:
                    arr_items['items'] = ["Not Mentioned"]

            if (arr_items['category'] == 'Work Experience' and len(arr_items)==4):
                temp = []

                for i in arr_items['items']:
                    if (len(i.split(", ")) == 4):
                        components = i.split(", ")
                        result = f"{components[0]}, {components[1]},{process_date(components[3])}"
                        temp.append(result)
                arr_items['items'] = temp
                if len(arr_items['items']) == 0:
                    arr_items['items'] = ["Not Mentioned"]

            elif arr_items['category'] == 'Work Experience':
                temp = []

                for i in arr_items['items']:
                    if (len(i.split(", ")) == 3):
                        components = i.split(", ")
                        result = f"{components[0]}, {components[1]},{process_date(components[2])}"
                        temp.append(result)
                arr_items['items'] = temp
                if len(arr_items['items']) == 0:
                    arr_items['items'] = ["Not Mentioned"]
            if(arr_items['category'].lower()=='skills' and len(arr_items['items'])==1):
                try:
                    
                    print("/////////////////////////skills")
                    print("/////////////////////////skills")
                    print("/////////////////////////skills")
                    arr_items['items']=arr_items['items'][0].split(', ')
                except Exception as e:
                    print(" Exception "+ str(e))

            if(arr_items['category'].lower()=='certifications' and len(arr_items['items'])==1):
                try:
                    
                    print("/////////////////////////skills")
                    print("/////////////////////////skills")
                    print("/////////////////////////skills")
                    arr_items['items']=arr_items['items'][0].split(', ')
                except Exception as e:
                    print(" Exception "+ str(e))

            if(arr_items['category'].lower()=='languages' and len(arr_items['items'])==1):
                try:
                    
                    print("/////////////////////////skills")
                    print("/////////////////////////skills")
                    print("/////////////////////////skills")
                    arr_items['items']=arr_items['items'][0].split(', ')
                except Exception as e:
                    print(" Exception "+ str(e))
                    

    return response_data


def is_valid_month(month):
    return re.match(r'^(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)$', month, re.IGNORECASE) is not None


def process_date(date):
    date=date.replace("/"," ")
    date_parts = date.split('-')
    print(date_parts)
    for idx, item in enumerate(date_parts):
        if item != 'Not Mentioned':
            if len(item.strip()) == 3:
                date_parts[idx] = 'Not Mentioned'
            elif len(item.strip()) == 4:
                date_parts[idx] = 'Not Mentioned'
            elif item == '':
                date_parts[idx] = 'Not Mentioned'
    s = ""
    for idx, string in enumerate(date_parts):
        s = s + string
        if (idx == 0):
            s = s + "- "

    return s


def remove_line_breaks(value):
    print("cleaning")
    return ' '.join(value.splitlines())


def ner_stream(bytes_data):
    text = analyze_read(bytes_data)
    prompt = cv_review_prompt.format(resume=text)
    response = openai().Completion.create(
        engine="ex-turbo-instruct",
        prompt=prompt,
        temperature=0.1,
        max_tokens=tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    response_text = response["choices"][0]["text"]
    return response["choices"][0]["text"]


def ner_stream_confidence(bytes_data):
    text = analyze_read(bytes_data)
    prompt = cv_review_prompt_confidence.format(resume=text)
    print(prompt)
    response = openai().Completion.create(
        engine="ex-turbo-instruct",
        prompt=prompt,
        temperature=0.1,
        max_tokens=tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    response_text = response["choices"][0]["text"]
    print("OCR////////////////////////////")
    print(response_text)
    print("OCR////////////////////////////")
    json_response = create_json_response(response_text)
    return create_json_response(response_text)



def job_confidence_task_chat(data):
    try:
        # print(data["pdf"])
        # print(data["positions"])
        response_resume = ner_stream_confidence_v2_chat(analyze_read(data["pdf"]))
        resume = json.loads(response_resume)['data']
        
        print("//////////////resume")
        print("//////////////resume")
        print(resume)
        print("//////////////resume")
        print("//////////////resume")
        # print(response_resume)

        skills = prepare_skills(resume)
        # print("//////////////skills")
        # print("//////////////skills")
        # print("//////////////skills")
        # print(skills)
        # print("//////////////skills")
        # print("//////////////skills")
        # print("//////////////skills")
        responses = ""
        for item in data["positions"]:
            prompt = cv_job_review_prompt_confidence.format(resume=skills, Positions=item.qualifications,
                                                            name=item.name, recruitment_id=item.recruitment_id)
            # print(prompt)
            response = openai_chat().chat.completions.create(
                model=model_name,
                messages=[
                    {"role":"system","content":"You are an AI  assistant that do what users tell you , confidence always should be lowercase c like this -confidence , do not write an explanation stick to the output format."},
                    {"role":"user","content":prompt}
                ],
                temperature=0.24,
                max_tokens=small_token,
                top_p=0.2,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None)
            responses += response.choices[0].message.content
            responses += "\n"

        response_text = responses
        print(response_text)
        json_response = create_json_response(response_text)
        positions = json.loads(json_response)['data']
        positions = [
            {
                'category': entry['category'],
                'items': [item.strip() for sublist in [item.replace("Name: ", '').split(",") for item in entry['items']] for
                        item in sublist],
                'confidence': entry['confidence']
            }
            for entry in positions
        ]
        ps = []
        try:
            if (len(positions) > 3):
                ps = sorted(positions, key=lambda x: x['confidence'], reverse=True)
                ps = ps[:3]
        except Exception as e:
            print("-------------Exception catched:\n" + e.__str__())
        print(resume + ps)

        return resume + ps
    except Exception as e:
        print(" Exception "+ str(e))
        return [{"error":1}]







def job_confidence_task(data):
    # print(data["pdf"])
    # print(data["positions"])
    response_resume = ner_stream_confidence_v2(analyze_read(data["pdf"]))
    resume = json.loads(response_resume)['data']
    skills = prepare_skills(resume)
    responses = ""
    for item in data["positions"]:
        prompt = cv_job_review_prompt_confidence.format(resume=skills, Positions=item.qualifications,
                                                        name=item.name, recruitment_id=item.recruitment_id)
        response = openai().Completion.create(
            engine="ex-turbo-instruct",
            prompt=prompt,
            temperature=0.24,
            max_tokens=tokens,
            top_p=0.2,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        responses += response['choices'][0]['text']
        responses += "\n"

    response_text = responses
    json_response = create_json_response(response_text)
    positions = json.loads(json_response)['data']
    positions = [
        {
            'category': entry['category'],
            'items': [item.strip() for sublist in [item.replace("Name: ", '').split(",") for item in entry['items']] for
                      item in sublist],
            'confidence': entry['confidence']
        }
        for entry in positions
    ]
    if (len(positions) > 3):
        positions = sorted(positions, key=lambda x: x['confidence'], reverse=True)
        positions = positions[:3]
    return resume + positions

def paginate_list(input_list, page_size):
    for start in range(0, len(input_list), page_size):
        yield input_list[start:start + page_size]
async def ner_job_confidence(pdf, positions):
    # with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:.
    finals = []
    for page in paginate_list(pdf, 5):
        time.sleep(0.5)
        with ThreadPoolExecutor(max_workers=100) as executor:
            # results = [executor.submit(job_confidence_task, _pdf, positions) for _pdf in pdf]
            for result in executor.map(job_confidence_task, [{'pdf': _pdf, 'positions': positions} for _pdf in page]):
                finals.append(result())

    return finals

async def ner_job_confidence_chat(pdf, positions):
    # with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:.
    finals = []
    for page in paginate_list(pdf, 100):
        time.sleep(1)
        with ThreadPoolExecutor(max_workers=100) as executor:
            # results = [executor.submit(job_confidence_task, _pdf, positions) for _pdf in pdf]
            for result in executor.map(job_confidence_task_chat, [{'pdf': _pdf, 'positions': positions} for _pdf in page]):
                if (len(result)>1):
                    finals.append(result)
    return finals



async def ner_job_confidence_chat_llm(pdf, positions):
    # with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:.
    finals = []
    for page in paginate_list(pdf, 100):
        time.sleep(1)
        with ThreadPoolExecutor(max_workers=100) as executor:
            # results = [executor.submit(job_confidence_task, _pdf, positions) for _pdf in pdf]
            for result in executor.map(job_confidence_task_chat_llm, [{'pdf': _pdf, 'positions': positions} for _pdf in page]):
                if (len(result)>1):
                    finals.append(result)
    return finals


def prepare_skills(resume):
    text = ""
    for arr_items in resume:
        print(arr_items['category'])
        if arr_items['category'].lower() == 'skills':
            text += f"-{arr_items['category']}: \n"
            text += f"{' ,'.join(arr_items['items'])} +\n"
        elif arr_items['category'].lower() == 'work experience':
            text += f"-{arr_items['category']}: \n"
            text += f"{' ,'.join(arr_items['items'])} \n"
        elif arr_items['category'].lower() == 'education':
            text += f"-{arr_items['category']}: \n"
            text += f"{' ,'.join(arr_items['items'])} \n"
        elif arr_items['category'].lower() == 'certifications':
            text += f"-{arr_items['category']}: \n"
            text += f"{' ,'.join(arr_items['items'])} \n"
    return text


def ner_stream_confidence_v2_chat(text):
    prompt = cv_review_prompt_confidence.format(resume=text)
    response = openai_chat().chat.completions.create(
        model=model_name,
        messages=[
            {
                "role":"system","content":"""you are AI CV analyser , 
Instructions: 
in work experience and education extract dates,in work experience
only include this 3 in work experience 'job title, company, dates' no more than that (do not mention country or city in work experience) for example Consultant , X company , Jan 2010 - feb 2015.
in education include 'Major,Degree,University,start date-end date' no more than that and no less, and  if major  or degree or university are not mentioned write Not Mentioned.
also the confidence value should be the accuracy of extracting the data and try to vary the confidence value not all of them are 100%.
                ------------------------------------------------------------------
Follow this format:
Work Experience:
- Job title, Company, start year - end year
- Confidence: Percentage of  how certain you are that the extracted data match the categories correctly %

Education:
- Major (Not Mentioned if not available), Degree type (Not Mentioned if not available), Institution (Not Mentioned if not available), Start date - End date
- Confidence: Percentage of  how certain you are that the extracted data match the categories correctly %

Skills:
- Specific skills
- Confidence: Percentage of  how certain you are that the extracted data match the categories correctly %

Certifications:
- Certifications earned
- Confidence: Percentage of how certain you are that the extracted data match the categories correctly %

Languages:
- Languages spoken, proficiency level 
- Confidence: Percentage of  how certain you are that the extracted data match the categories correctly %

Personnel info:
-first name: write first name
-last name: write last name
-address: write address
-phone numbe: write phone number
-email: write email
-Confidence: Percentage of accuracy of extracting the info %
------------------------------------------------------------------------------
please because i want consistent information always follow this format and in order split major and degree if needed to have this format 'Major , Degree , University , start date-end date in (Education) and if start year not mentioned write not mentioned and same for end year write not mentioned and if both not mentioned write Not Mentioned - Not Mentioned. and seperate degree and degree type and for each if not available or not mentioned write Not Mentioned 
and if both not mentioned write Not Mentioned, Not Mentioned, Institution, start year - end year. N.B: ALWAYS SEPERATE MAJOR AND DEGREE and write Not mentioned if they are not mentioned for each one and always write Start date - End date and same as work expereiene if one date is not available write Not Mentioned. start year and end year should be in this format MM yyyy for example jan 2020.
and Work Experience if start year not mentioned write not mentioned and same for end year write not mentioned and if both not mentioned write Not Mentioned - Not Mentioned, focus on the global information about professional experience and include personnel information, educational background, skills, certifications, and languages spoken. Stick strictly to these instructions and categories, keeping the information concise and anonymous.
 The confidence percentages should reflect how certain you are that the extracted data match the categories correctly (do not stick the the value in the example) and do not include any of the fake or incorrect details.
 important: in work experience and education the start date and end date if one of the month or year not mentioned the whole date should be Not Mentioned. always month should first 3 letters not numbers like 06/2020 or 12/2021 i want it JUN 2020 or DEC 2021 in both Work Experience and Education. and date always should be MM YYYY if MM or YYYY is missing write the date Not Mentioned even if one of them is written for example if year is Mentioned without Month write not Mentioned because i always want this format MM YYYY or Not Mentioned.
in education do not mention the country or city. and all the dates should follow this format JAN 2020 ."""
            },
            {"role":"user","content":prompt}
        ],
        temperature=0,
        max_tokens=tokens,
        top_p=0.4,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    print(prompt)
    response_text = response.choices[0].message.content
    print("OCR//////////////////////////// chat")
    print(response_text)
    print("OCR////////////////////////////chat")
    response2=openai_chat().chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role":"system","content":"""you have this task to correct a part of a given text to make it follow a specific format chosen by the user."""},
    {"role":"user","content":f"""
    ----------------------------------------------
    given text: {response_text}
    ----------------------------------------------
    i want you to fix the education part in the given text to follow this format:
    Education:
    - Major (Not Mentioned if not available), Degree type (Not Mentioned if not available), Institution (Not Mentioned if not available), Start date - End date
    - Confidence: Percentage of  how certain you are that the extracted data match the categories correctly %
    --------------------------------------------------
    do not mention city or country in education.
    output the same text but with education fixed.
Given text after correction:
    """} 
            ],
            temperature=0,
            max_tokens=tokens,
            top_p=0,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
    fixed_response=response2.choices[0].message.content
    fixed_response=fixed_response.replace("Given text after correction:","")
    fixed_response=fixed_response.replace("given text:","")
    fixed_response=fixed_response.replace("Given text:","")
    print("OCR////////////////////////////fixed chat")
    print(fixed_response)
    print("OCR////////////////////////////fixed chat")
        # //////////////////////
    return create_json_response(fixed_response)


def ner_stream_confidence_v2(text):
    prompt = cv_review_prompt_confidence.format(resume=text)
    response = openai().Completion.create(
        engine="ex-turbo-instruct",
        prompt=prompt,
        temperature=0,
        max_tokens=tokens,
        top_p=0,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    print(prompt)
    response_text = response["choices"][0]["text"]
    print("OCR////////////////////////////")
    print(response_text)
    print("OCR////////////////////////////")
    return create_json_response(response_text)





def job_confidence_task_chat_llm(data):
    try:
        # response_resume = ner_stream_confidence_v2_chat(analyze_read(data["pdf"]))
        resume = resume_parser(analyze_read(data["pdf"]))
        # print("/////////resume llm")
        # print(resume)
        # print("/////////resume llm")
        # skills = prepare_skills(resume)
        responses = ""
        for item in data["positions"]:
            prompt = cv_job_review_prompt_confidence.format(resume=resume, Positions=item.qualifications,
                                                            name=item.name, recruitment_id=item.recruitment_id)

            response = openai_chat().chat.completions.create(
                model=model_name,
                messages=[
                    {"role":"system","content":"You are an AI  assistant that do what users tell you , confidence always should be lowercase c like this -confidence , do not write an explanation stick to the output format."},
                    {"role":"user","content":prompt}
                ],
                temperature=0.24,
                max_tokens=small_token,
                top_p=0.2,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None)
            responses += response.choices[0].message.content
            responses += "\n"

        response_text = responses
        # print(response_text)
        json_response = create_json_response(response_text)
        positions = json.loads(json_response)['data']
        positions = [
            {
                # 'category': entry['category'],
                'items': [item.strip() for sublist in [item.replace("Name: ", '').split(",") for item in entry['items']] for
                        item in sublist],
                'confidence': entry['confidence']
            }
            for entry in positions
        ]
        ps = []
        try:
            if (len(positions) > 3):
                ps = sorted(positions, key=lambda x: x['confidence'], reverse=True)
                ps = ps[:3]
        except Exception as e:
            print("-------------Exception catched:\n" + e.__str__())
        # print(resume + ps)

        return {"resume":resume ,"positions": ps}
    except Exception as e:
        print(" Exception "+ str(e))
        return [{"error":1}]