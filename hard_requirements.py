import json
import re
from dotenv import load_dotenv
from openai import AzureOpenAI
import os

# Load environment variables from the .env file
load_dotenv()

# Azure OpenAI credentials from the .env file
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

# Azure OpenAI client initialization
openclient = AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=api_key,
    api_version=api_version
)

def clean_gpt_output(gpt_output):
    """Clean and standardize GPT-4 output to ensure valid JSON."""
    try:
        # Ensure no trailing commas in JSON arrays or objects
        gpt_output = re.sub(r',\s*([\]}])', r'\1', gpt_output)  # Remove trailing commas

        # Correct improperly quoted JSON arrays
        gpt_output = re.sub(r'"\[', '[', gpt_output)  # Replace "[ with [
        gpt_output = re.sub(r'\]"', ']', gpt_output)  # Replace ]" with ]

        # Replace escaped quotes within strings
        gpt_output = gpt_output.replace('\\"', '"')

        # Strip unnecessary newlines or spaces
        gpt_output = gpt_output.strip()

        return gpt_output
    except Exception as e:
        print(f"Error cleaning GPT output: {e}")
        return gpt_output  # Return as-is if cleaning fails
    

def extract_email_data(json_response):
    """Extract only the data starting from 'email' key onwards."""
    try:
        # Parse the JSON response
        data = json.loads(json_response)
        # Ensure 'filtered_results' key exists and extract the list
        if "filtered_results" in data and isinstance(data["filtered_results"], list):
            return data["filtered_results"]
        else:
            raise KeyError("'filtered_results' key is missing or not a list in the response.")
    except Exception as e:
        print(f"Error extracting email data: {e}")
        return None

def filter_by_hard_requirements(results, hard_requirements):
    try:
        # Validate inputs
        if not hard_requirements or not all(isinstance(req, str) for req in hard_requirements):
            raise ValueError("Hard requirements should be a non-empty list of strings.")
        if not isinstance(results, list) or not results:
            raise ValueError("Query results should be a non-empty list.")

        # Prepare the prompt for GPT-4
        gpt_input = {
            "hard_requirements": hard_requirements,
            "query_results": results,
        }

        # Azure OpenAI GPT-4 call
        response = openclient.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in job analysis and resume filtering."},
                {
                    "role": "user",
                    "content": (
                        f"Filter the provided query results based on the following hard requirements:\n\n"
                        f"{json.dumps(gpt_input, indent=2)}\n\n"
                        f"Return the results in JSON format only, starting directly from the list of objects. dont include an characters like ```json before outputting the json "
                        f"Do not include the 'filtered_results' wrapper. Ensure the JSON is valid and properly formatted."
                    )
                }
            ],
            max_tokens=4000,
            temperature=0.5
        )

        # Extract the response content
        gpt_response = response.choices[0].message.content
        print("Raw GPT Response:", gpt_response)  # Debugging step
        
        # Clean the GPT response
        cleaned_response = clean_gpt_output(gpt_response)
        print("Cleaned Response:", cleaned_response)  # Debugging step

        # Parse the cleaned response directly
        try:
            email_data = json.loads(cleaned_response)
            return email_data
        except json.JSONDecodeError as e:
            print(f"Error parsing cleaned response to JSON: {e}")
            return None

    except Exception as e:
        print(f"Error in filtering with GPT-4: {e}")
        return None
