import requests

def get_plugins(chris_url: str, username: str, password: str) -> dict:
    """List all plugins from ChRIS."""
    url = f"{chris_url}/api/v1/plugins/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()
    return response.json()

def get_plugin_instance_details(chris_url: str, username: str, password: str, instance_id: int) -> dict:
    """Get details of a specific plugin instance by ID."""
    url = f"{chris_url}/api/v1/plugins/instances/{instance_id}/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()

    items = response.json().get("collection", {}).get("items", [])
    if not items:
        return {"error": "Plugin instance not found"}

    # Flatten the item["data"] list into a dict
    data = items[0].get("data", [])
    return {entry["name"]: entry["value"] for entry in data}
