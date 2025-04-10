import streamlit as st
import base64
from dotenv import load_dotenv
import os
load_dotenv()

import json
import re
import string
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
import unicodedata
import requests


# Azure Blob Storage credentials
blob_connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
container_name = "cv-data"  # Azure Blob Storage container name

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Azure Form Recognizer credentials
endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
form_recognizer_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))


# Utility Functions
def upload_to_blob(file_name, file_content):
    """Uploads a file to Azure Blob Storage."""
    try:
        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_content, overwrite=True)
        st.success(f"Uploaded {file_name} to Azure Blob Storage.")
    except Exception as e:
        st.error(f"Error uploading file to Blob Storage: {e}")


def list_blob_files():
    """Lists all files in the Azure Blob Storage container."""
    try:
        return [blob.name for blob in container_client.list_blobs()]
    except Exception as e:
        st.error(f"Error listing files in Blob Storage: {e}")
        return []


def convert_pdf_to_base64(pdf_content):
    """Converts PDF content to Base64."""
    try:
        return base64.b64encode(pdf_content).decode("utf-8")
    except Exception as e:
        st.error(f"Error converting PDF to Base64: {e}")
        return None


def call_api_with_raw_data(url, data):
    """Calls external API with raw JSON data."""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling API: {e}")
        return None


def save_response_as_json(response_data, file_name):
    """Saves API response as a JSON file in cv_outputs directory."""
    try:
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w") as file:
            json.dump(response_data, file, indent=4)
        st.write(f"Response saved as JSON: {file_name}")
    except Exception as e:
        st.error(f"Error while saving response as JSON: {e}")


def analyze_document(document_path, client):
    """Analyzes a document using Azure Form Recognizer."""
    try:
        with open(document_path, "rb") as f:
            poller = client.begin_analyze_document("prebuilt-read", document=f)
        return poller.result()
    except HttpResponseError as e:
        st.error(f"Error analyzing document: {e}")
        return None


def sanitize_filename(filename):
    """Sanitizes the filename."""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars).replace(' ', '_').replace('/', '_')


def display_pdf_from_blob(blob_name):
    """Displays PDF from Azure Blob Storage in Streamlit."""
    try:
        # Get the blob client and download the blob
        blob_client = container_client.get_blob_client(blob_name)
        pdf_data = blob_client.download_blob().readall()

        # Convert the PDF data to base64 and display it in the PDF viewer
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"
        
        st.write(f"**Displaying PDF: {blob_name}**")
        st.markdown(f'<embed src="{pdf_data_uri}" width="800" height="600" type="application/pdf">', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error displaying PDF {blob_name}: {e}")


# Streamlit App
def cv_analysis_page():
    st.title("CV Database")

    # File upload sections
    uploaded_files = st.file_uploader("Upload CVs (PDF)", accept_multiple_files=True, type=['pdf'])

    if st.button("Analyze"):
        if uploaded_files:
            output_directory = "cv_outputs"
            os.makedirs(output_directory, exist_ok=True)

            pdf_json_files = []

            for uploaded_file in uploaded_files:
                st.write(f"Processing CV: {uploaded_file.name}...")

                # Upload PDF to Azure Blob Storage
                upload_to_blob(uploaded_file.name, uploaded_file.getvalue())

                # Convert PDF to base64
                pdf_content = uploaded_file.read()
                base64_pdf = convert_pdf_to_base64(pdf_content)

                if base64_pdf:
                    api_url = "http://localhost:7071/resume/v1/ner-job-confidence-new"
                    response_data = call_api_with_raw_data(api_url, {"pdf": [base64_pdf]})

                    if response_data:
                        cv_name = os.path.splitext(uploaded_file.name)[0]
                        json_output_path = f"{output_directory}/{cv_name}.json"
                        save_response_as_json(response_data, json_output_path)
                        pdf_json_files.append(json_output_path)

            st.write("PDF JSON Files:")  # Displaying the JSON files
            st.write(pdf_json_files)

    # File listing and displaying PDFs from Azure Blob Storage as dropdown
    pdf_files = list_blob_files()

    if pdf_files:
        selected_pdf = st.selectbox("Select a CV from Blob Storage", pdf_files)

        if selected_pdf:
            if selected_pdf.endswith(".pdf"):  # Only show PDF files
                display_pdf_from_blob(selected_pdf)
    else:
        st.write("No PDFs found in Blob Storage.")