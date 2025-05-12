import requests
from flask import current_app

def get_external_data(endpoint):
    base_url = current_app.config['EXTERNAL_API_BASE_URL']
    api_key = current_app.config['EXTERNAL_API_KEY']
    headers = {'Authorization': f'Bearer {api_key}'}

    response = requests.get(f"{base_url}/{endpoint}", headers=headers)
    response.raise_for_status()
    return response.json()