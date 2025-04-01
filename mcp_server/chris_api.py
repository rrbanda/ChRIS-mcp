import requests

# Function to get the list of plugins from ChRIS
def get_plugins(chris_url: str, username: str, password: str) -> dict:
    url = f"{chris_url}/api/v1/plugins/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()  # Raise an error if the status code is not 200
    return response.json()  # Return the response as a JSON object

# Function to get details of a specific plugin instance by its ID
def get_plugin_instance_details(chris_url: str, username: str, password: str, instance_id: int) -> dict:
    url = f"{chris_url}/api/v1/plugins/instances/{instance_id}/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()

    # Extract the items from the response
    items = response.json().get("collection", {}).get("items", [])
    if not items:
        return {"error": "Plugin instance not found"}  # Handle the case when no instance is found
    
    # Flatten the item["data"] list into a dict
    data = items[0].get("data", [])
    return {entry["name"]: entry["value"] for entry in data}  # Return plugin instance details as a dictionary

# Function to get the list of PACS files
def get_pacs_files(chris_url: str, username: str, password: str) -> dict:
    url = f"{chris_url}/api/v1/pacs/files/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()
    return response.json()

# Function to get the list of user files
def get_user_files(chris_url: str, username: str, password: str) -> dict:
    url = f"{chris_url}/api/v1/userfiles/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()
    return response.json()

# Function to get a list of pipelines
def get_pipelines(chris_url: str, username: str, password: str) -> dict:
    url = f"{chris_url}/api/v1/pipelines/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()
    return response.json()

# Function to get details of a specific pipeline by its ID
def get_pipeline_details(chris_url: str, username: str, password: str, pipeline_id: int) -> dict:
    url = f"{chris_url}/api/v1/pipelines/{pipeline_id}/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()
    return response.json()

# Function to search for a specific plugin or resource
def search_plugins(chris_url: str, username: str, password: str, query: dict) -> dict:
    url = f"{chris_url}/api/v1/plugins/search/"
    response = requests.get(url, params=query, auth=(username, password))
    response.raise_for_status()
    return response.json()

# Function to create a new pipeline
def create_pipeline(chris_url: str, username: str, password: str, pipeline_data: dict) -> dict:
    """Creates a new pipeline in ChRIS."""
    url = f"{chris_url}/api/v1/pipelines/"
    response = requests.post(url, json=pipeline_data, auth=(username, password))
    response.raise_for_status()
    return response.json()
