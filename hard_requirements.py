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
    """Clean the GPT-4 output by removing unwanted characters after JSON."""
    # Remove any unwanted text such as 'json' or code block markers
    gpt_output = re.sub(r'(?i)^.*json[^\{]*', '', gpt_output)  # Remove leading text before JSON

    # Remove any extraneous non-whitespace characters after the closing brace
    gpt_output = re.sub(r'}\s*[^}]*$', '}', gpt_output)  # Ensure only the valid JSON is retained after '}'

    # Ensure there are no backticks or code block markers left
    gpt_output = re.sub(r'^[`]+', '', gpt_output)  # Remove backticks at the beginning
    gpt_output = re.sub(r'[`]+$', '', gpt_output)  # Remove backticks at the end

    # Clean up escaped quotes within the string
    gpt_output = re.sub(r'\\\"', '"', gpt_output)

    # Return cleaned output, trimming any unwanted whitespace at the ends
    return gpt_output.strip()

def parse_json_output(gpt_response):
    """Parse the cleaned GPT output to JSON."""
    cleaned_response = clean_gpt_output(gpt_response)

    try:
        # Try to parse the cleaned response into JSON
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print(f"Error decoding GPT-4 response: {e}")
        print(f"Raw cleaned response content: {cleaned_response}")
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
                        f"Return the results in JSON format only dont add any other characters or words ensure response is proper json format"
                        f"To fix the provided JSON structure so that it is valid, you need to properly format the arrays (education, certifications, work_experience, and skills) by removing the extra quotation marks around them"
                    )
                }
            ],
            max_tokens=1000,
            temperature=0.5
        )

        # Correct way to access the content from the response
        gpt_response = response.choices[0].message.content
        print(gpt_response)
        # Clean the GPT response to remove unwanted text and code block markers
        cleaned_response = clean_gpt_output(gpt_response)
        print(cleaned_response)
        # Return the cleaned response directly (as a raw JSON string)
        if cleaned_response:
            return cleaned_response
        else:
            print("Received an empty response from GPT-4.")
            return ''

    except Exception as e:
        print(f"Error in filtering with GPT-4: {e}")
        return ''