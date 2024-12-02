import json
from fuzzywuzzy import fuzz
from openai import AzureOpenAI
import csv  # Add missing CSV import

# Azure OpenAI credentials
openclient = AzureOpenAI(
    azure_endpoint="https://ex-openaigpt4.openai.azure.com/",
    api_key="b2b2b4f3fca240409bce99def523d41e",
    api_version="2024-02-01"
)

# Function to extract skills from query results
def load_skills_from_query_results(query_results):
    """Extract and aggregate skills from query results."""
    skills = []
    try:
        results = json.loads(query_results)  # Parse the query results JSON
        for result in results:
            # Ensure 'skills' exists and is formatted as a list
            if "skills" in result and isinstance(result["skills"], list):
                skills.extend(result["skills"])
        return list(set(skills))  # Remove duplicates
    except json.JSONDecodeError as e:
        print(f"Error parsing query results: {e}")
        return []
    except KeyError as e:
        print(f"Key error while extracting skills: {e}")
        return []

# Function to save matching score to CSV
def save_matching_score_to_csv(file_name, matching_score):
    """Save matching score to a CSV file."""
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['CV', 'Matching Score'])
        writer.writerow(['Overall', f"{matching_score:.2f}"])

import re

def clean_gpt_output(gpt_output):
    """Clean the GPT-4 output by removing unwanted characters such as 'json' or code block markers."""
    # Remove any unwanted text such as 'json' or backticks before the actual JSON
    gpt_output = re.sub(r'(?i)^.*json[^\{]*', '', gpt_output)  # Remove 'json' and any leading characters before the JSON
    gpt_output = re.sub(r'^[`]+', '', gpt_output)  # Remove backticks at the beginning
    gpt_output = re.sub(r'[`]+$', '', gpt_output)  # Remove backticks at the end
    return gpt_output.strip()  # Remove leading/trailing whitespace





# Function to extract job information using Azure OpenAI
def extract_job_information(job_description):
    """Extract structured job information from a job description."""
    template = """{
        "Job Title": "",
        "Location": "",
        "Work Type": "",
        "Industry": "",
        "Education": "",
        "Years of Experience": "",
        "Skills"(keep skills short no extra words ie python, matlab, excel...): "",
        "Abilities": "",
        "Certifications": ""
    }"""

    response = openclient.chat.completions.create(
        model="gpt-4",
        messages=[ 
            {"role": "system", "content": "You are an expert in job analysis."},
            {"role": "user", "content": f"Extract job information using this template: {template}\n\nParagraph: {job_description} Make sure the format is pure JSON. Don't add any characters or letters before the JSON."}
        ],
        max_tokens=1000
    )

    response_content = response.choices[0].message.content.strip()
    print("Raw GPT Output:", response_content)

    # Clean the GPT output
    cleaned_output = clean_gpt_output(response_content)
    print("Cleaned GPT Output:", cleaned_output)

    try:
        return json.loads(cleaned_output)  # Parse the cleaned JSON string
    except json.JSONDecodeError:
        print("Failed to parse job information response.")
        return None
