from apis.openai import get_openai as openai
from apis.openai import get_openai_chat as openai_chat
from apis.functions import split
from models.JobDescription import JobDescription
from prompts.main import extract_degree, highlights, job_description_prompt#job_description_prompt_json
import os
import json
model_name=os.environ.get("OPENAI_CHAT_MODEL_NAME")
tokens = 400
def get_job_offer_chat(request: JobDescription):
    prompt = job_description_prompt.format(**request.__dict__)
    response = openai_chat().chat.completions.create(
        model=model_name,
        messages=[
            {"role":"system","content":"you are AI HR who helps at creating jobs description after each key should be a new line for example in title: here should be a newline"},
            {"role":"user","content":prompt}
            ],
        temperature=0,
        max_tokens=tokens,
        top_p=0,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)

    response_text = response.choices[0].message.content
    
    
    data = split(response_text)
    # return data
    # data=json.loads(response.choices[0].message.content)
    # print(data)
    if data.__contains__("Certifications"):
        data['Certifications'] = data['Certifications'].removeprefix("-").split("\n-")
        data['Certifications'] = [item.replace('\n', '').lstrip() for item in data['Certifications']]
    else:
        data['Certifications'] = []
    prompt = highlights.format(text=data["Responsibilities"])

    response2 = openai_chat().chat.completions.create(
        model=model_name,
        messages=[
            {"role":"system","content":"you are AI assistant that helps extract highlights from a given text"},
            {"role":"user","content":prompt}
        ],
        temperature=0.1,
        max_tokens=tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
    response3 = openai_chat().chat.completions.create(
        model=model_name,
        messages=[

            {"role":"system","content":"""you are AI assistant that helps extract degree , field , years from a given text , years should be only a number 0 if not available without writing description
Instructions:
the output format should like this :
- Level: degree
- Field: Major
- Years: 0  
"""},
            {"role":"user","content":extract_degree.format(text=data["Requirements"])}
        ],
        temperature=0.1,
        max_tokens=tokens,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
# extract_degree.format(text=data["Requirements"])
    response_text = response2.choices[0].message.content
    response_text = response_text.removeprefix("-").split("\n-")
    response_text = [item.replace('\n', '').lstrip() for item in response_text]
    data["Skills"] = response_text
    resp3_text = response3.choices[0].message.content
    # return resp3_text
    resp3_text = resp3_text.removeprefix("-").split("\n-")
    resp3_text = [item.replace('\n', '').lstrip() for item in resp3_text]
    resp3_text = [item.replace('+', '').lstrip() for item in resp3_text]
    # resp3_text=resp3_text.replace("[","")
    # resp3_text=resp3_text.replace("]","")
    resp3_dict = {}
    ls_keywords = ["Level", "Field", "Years"]
    print("//////////////////")
    print("//////////////////")
    print("//////////////////")
    print("//////////////////")
    print(response3.choices[0].message.content)
    print("type")
    print(type(response3.choices[0].message.content))
    print("//////////////////")
    print("//////////////////")
    print("//////////////////")
    for i in resp3_text:
        for key in ls_keywords:
            if key in i:
                if key.lower() == "years":
                    resp3_dict[key] = int(i.replace(f'{key}: ', ''))
                else:
                    resp3_dict[key] = i.replace(f'{key}: ', '')
    # resp3_dict=json.loads(response3.choices[0].message.content)

    data["Degree"] = resp3_dict
    return data

# ////////////////////////////////////////////////////////
# ////////////////////////////////////////////////////

def get_job_offer(request: JobDescription):
    prompt = job_description_prompt.format(**request.__dict__)
    response = openai().Completion.create(
        engine="ex-turbo-instruct",
        prompt=prompt,
        temperature=0.1,
        max_tokens=tokens,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)

    response_text = response["choices"][0]["text"]
    data = split(response_text)
    
    if data.__contains__("Certifications"):
        data['Certifications'] = data['Certifications'].removeprefix("-").split("\n-")
        data['Certifications'] = [item.replace('\n', '').lstrip() for item in data['Certifications']]
    else:
        data['Certifications'] = []
    prompt = highlights.format(text=data["Responsibilities"])

    response2 = openai().Completion.create(
        engine="ex-turbo-instruct",
        prompt=prompt,
        temperature=0.1,
        max_tokens=tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
    response3 = openai().Completion.create(
        engine="ex-turbo-instruct",
        prompt=extract_degree.format(text=data["Requirements"]),
        temperature=0.1,
        max_tokens=tokens,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)

    response_text = response2["choices"][0]["text"]
    response_text = response_text.removeprefix("-").split("\n-")
    response_text = [item.replace('\n', '').lstrip() for item in response_text]
    data["Skills"] = response_text
    resp3_text = response3["choices"][0]["text"]
    resp3_text = resp3_text.removeprefix("-").split("\n-")
    resp3_text = [item.replace('\n', '').lstrip() for item in resp3_text]
    resp3_text = [item.replace('+', '').lstrip() for item in resp3_text]
    resp3_dict = {}
    ls_keywords = ["Level", "Field", "Years"]

    for i in resp3_text:
        for key in ls_keywords:
            if key in i:
                if key.lower() == "years":
                    resp3_dict[key] = int(i.replace(f'{key}: ', ''))
                else:
                    resp3_dict[key] = i.replace(f'{key}: ', '')
    data["Degree"] = resp3_dict
    return data
