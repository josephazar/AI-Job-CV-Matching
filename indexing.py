from dotenv import load_dotenv
import os
load_dotenv()

import json
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataSourceConnection,
    SearchIndexer,
    FieldMapping,
    SearchIndex,
    SimpleField,
    SearchableField
)
import logging

# Load environment variables from the .env file
load_dotenv()

# Azure Blob Storage and Search credentials from the .env file
blob_connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = os.getenv("SEARCH_INDEX_NAME")
container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")
local_folder_path = os.getenv("LOCAL_FOLDER_PATH")
data_source_name = os.getenv("DATA_SOURCE_NAME")

# Initialize the BlobServiceClient for Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Initialize SearchIndexClient and SearchIndexerClient for Azure Cognitive Search
index_client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_api_key))
indexer_client = SearchIndexerClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_api_key))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_flattened(entry):
    """
    Check if a given resume entry is already flattened.
    """
    flattened_keys = {"work_experience", "skills", "certifications", "education", "phone_number", "email", "filename"}
    return flattened_keys.issubset(entry.keys())

def flatten_resume(resume):
    """
    Flatten the nested resume JSON into a flat structure suitable for Azure Search indexing.
    """
    try:
        flattened = {
            "work_experience": [
                f"{job['job_title']} at {job['company']} ({job.get('start_month', 'Not Mentionned')}/{job.get('start_year', 'Not Mentionned')} - {job.get('end_month', 'Not Mentionned')}/{job.get('end_year', 'Not Mentionned')})" 
                for job in resume.get("Work_Experience", {}).get("items", [])
            ],
            "skills": resume.get("Skills", {}).get("items", []),
            "certifications": resume.get("Certifications", {}).get("items", []),
            "education": [
                f"{edu['major']} at {edu['institution']} ({edu.get('start_year', 'Not Mentionned')} - {edu.get('end_year', 'Not Mentionned')})"
                for edu in resume.get("Education", {}).get("items", [])
            ],
            "phone_number": resume.get("Personnel_info", {}).get("phone_number", "Not Mentionned"),
            "email": resume.get("Personnel_info", {}).get("email", "Not Mentionned"),
            "filename": resume.get("filename", "Not Mentionned")
        }
        return flattened
    except Exception as e:
        print(f"Error flattening resume: {e}")
        return {}

def add_filename_and_flatten_json(file_path, filename):
    """
    Overwrite the file with a new JSON containing only flattened entries if not already flattened.
    """
    try:
        # Load JSON data from the original file
        with open(file_path, "r") as file:
            data = json.load(file)

        # Add filename without extension to each resume and flatten if necessary
        name_without_extension = os.path.splitext(filename)[0]
        updated_data = []

        if isinstance(data, list):
            for entry in data:
                if not is_flattened(entry):  # Only flatten if not already flattened
                    resume = entry.get("resume", {})
                    resume["filename"] = name_without_extension

                    # Flatten the resume and update entry
                    flattened_resume = flatten_resume(resume)
                    updated_data.append(flattened_resume)
                else:
                    updated_data.append(entry)  # Keep as is if already flattened

        # Overwrite the file with updated data
        with open(file_path, "w") as new_file:
            json.dump(updated_data, new_file, indent=4)

        print(f"File processed and saved: {file_path}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def upload_file_to_blob(file_path, filename):
    """
    Upload a file to Azure Blob Storage.
    """
    try:
        with open(file_path, "rb") as data:
            blob_client = container_client.get_blob_client(blob=filename)
            blob_client.upload_blob(data, overwrite=True)
            logger.info(f"File '{filename}' uploaded to Blob Storage.")
    except Exception as e:
        logger.error(f"Failed to upload file '{filename}' to Blob Storage: {e}")


def upload_json_files(local_folder_path):
    """
    Process all JSON files in the specified folder and upload them to Azure Blob Storage.
    """
    for filename in os.listdir(local_folder_path):
        if filename.endswith(".json"):  # Only process .json files
            file_path = os.path.join(local_folder_path, filename)

            # Update JSON file with the stripped filename and flatten structure if needed
            add_filename_and_flatten_json(file_path, filename)

            # Upload the processed file to Azure Blob Storage
            upload_file_to_blob(file_path, filename)

# Step 3: Create the search index (if not already created)
def create_index():
    fields = [
        SimpleField(name="id", type="Edm.String", key=True),  # Add a key field
        SearchableField(name="education", type="Collection(Edm.String)", filterable=True),  # education_major as collection
        SearchableField(name="skills", type="Collection(Edm.String)", filterable=True),  # skills as collection
        SearchableField(name="certifications", type="Collection(Edm.String)", filterable=True),  # certifications as collection
        SimpleField(name="phone_number", type="Edm.String"),
        SimpleField(name="email", type="Edm.String"),
        SearchableField(name="work_experience", type="Collection(Edm.String)"),  # Add work_experience field
        SearchableField(name="filename", type="Collection(Edm.String)")
    ]
    index = SearchIndex(name=index_name, fields=fields)
    index_client.create_or_update_index(index)
    logger.info(f"Index '{index_name}' created.")

# Step 4: Create the indexer to map the Blob data to the index
def create_indexer(data_source_name):
    field_mappings = [
        FieldMapping(source_field_name="work_experience", target_field_name="work_experience"),
        FieldMapping(source_field_name="skills", target_field_name="skills"),
        FieldMapping(source_field_name="certifications", target_field_name="certifications"),
        FieldMapping(source_field_name="education", target_field_name="education"),
        FieldMapping(source_field_name="phone_number", target_field_name="phone_number"),
        FieldMapping(source_field_name="email", target_field_name="email"),
        FieldMapping(source_field_name="filename", target_field_name="filename")
    ]
    indexer = SearchIndexer(
        name="resume-indexer",
        data_source_name=data_source_name,
        target_index_name=index_name,
        parameters={
            "configuration": {
                "parsingMode": "jsonArray"
            }
        },
        field_mappings=field_mappings
    )
    indexer_client.create_or_update_indexer(indexer)
    logger.info(f"Indexer created with data source: {data_source_name}")

def run_indexer():
    indexer_client.run_indexer("resume-indexer")
    logger.info("Indexer execution initiated.")

# Step 6: Query the indexed data (for demonstration)
def search_index():
    search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=AzureKeyCredential(search_api_key))

    # Example search query for job title
    results = search_client.search("Machine Learning Engineer")
    for result in results:
        logger.info(result)

    logger.info("Indexer has been executed and search results retrieved.")

if __name__ == "__main__":
    upload_json_files(local_folder_path)  # Upload JSON files to Blob Storage
    create_index()  # Create the index
    create_indexer(data_source_name)  # Create the indexer
    run_indexer()  # Run the indexer
    search_index()  # Search and display results
