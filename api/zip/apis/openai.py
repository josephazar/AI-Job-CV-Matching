import openai
from openai import AzureOpenAI
import os


def get_openai() -> openai:
    openai.api_type = os.environ.get('OPENAI_API_TYPE')
    openai.api_base = os.environ.get('OPENAI_API_BASE')
    openai.api_version = os.environ.get('OPENAI_API_VERSION')
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    return openai

def get_openai_chat() -> AzureOpenAI:
    client = AzureOpenAI(
    api_key = os.environ.get("OPENAI_CHAT_API_KEY"),  
    api_version = os.environ.get("OPENAI_CHAT_API_VERSION"),
    azure_endpoint = os.environ.get("OPENAI_CHAT_API_BASE")
    )   
    return client

# def get_openai_chat():
#     return ""
