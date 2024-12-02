import os
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


# Function to update the JSON files to include the filename without the extension
def add_filename_to_json(file_path, filename):
    # Strip the file extension
    name_without_extension = os.path.splitext(filename)[0]
    
    with open(file_path, "r") as file:
        data = json.load(file)

    # Add the stripped filename as a field in the `resume` object
    if isinstance(data, list) and "resume" in data[0]:
        data[0]["resume"]["filename"] = name_without_extension

    # Save the modified JSON back to the file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

# Function to upload JSON files to Azure Blob Storage
def upload_json_files():
    if not container_client.exists():
        container_client.create_container()

    for filename in os.listdir(local_folder_path):
        if filename.endswith(".json"):  # Only process .json files
            file_path = os.path.join(local_folder_path, filename)

            # Update JSON file with the stripped filename
            add_filename_to_json(file_path, filename)

            # Upload the updated JSON file to Azure Blob Storage
            blob_client = container_client.get_blob_client(filename)
            with open(file_path, "rb") as file_data:
                blob_client.upload_blob(file_data, overwrite=True)

            print(f"Uploaded: {filename}")

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
    print(f"Index '{index_name}' created.")

# Step 4: Create the indexer to map the Blob data to the index
def create_indexer(data_source_name):
    field_mappings = [
        # Mapping work experience directly as a collection of strings
        FieldMapping(source_field_name="work_experience", target_field_name="work_experience"),

        # Mapping skills directly as a collection of strings
        FieldMapping(source_field_name="skills", target_field_name="skills"),

        # Mapping certifications directly as a collection of strings
        FieldMapping(source_field_name="certifications", target_field_name="certifications"),

        # Mapping education directly as a collection of strings
        FieldMapping(source_field_name="education", target_field_name="education"),

        # Mapping phone number directly
        FieldMapping(source_field_name="phone_number", target_field_name="phone_number"),

        # Mapping email directly
        FieldMapping(source_field_name="email", target_field_name="email"),

        # Mapping filename directly
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
    print(f"Indexer created with data source: {data_source_name}")


def run_indexer():
    indexer_client.run_indexer("resume-indexer")
    print("Indexer execution initiated.")

# Step 6: Query the indexed data (for demonstration)
def search_index():
    search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=AzureKeyCredential(search_api_key))

    # Example search query for job title
    results = search_client.search("Machine Learning Engineer")
    for result in results:
        print(result)

    print("Indexer has been executed and search results retrieved.")


if __name__ == "__main__":
    upload_json_files()  # Upload JSON files to Blob Storage
    create_index()  # Create the index
    create_indexer(data_source_name)  # Create the indexer
    run_indexer()  # Run the indexer
    search_index()  # Search and display results
