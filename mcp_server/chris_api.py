import requests

# Function to get the list of plugins from ChRIS
def get_plugins(chris_url: str, username: str, password: str) -> dict:
    url = f"{chris_url}/api/v1/plugins/"
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()  # Raise an error if the status code is not 200
    return response.json()  # Return the response as a JSON object
