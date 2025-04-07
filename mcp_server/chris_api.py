import requests

CHRIS_URL = "http://localhost:8000"

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

    items = response.json().get("collection", {}).get("items", [])
    if not items:
        return {"error": "Plugin instance not found"}

    data = items[0].get("data", [])
    return {entry["name"]: entry["value"] for entry in data}

# Other functions can remain the same...
