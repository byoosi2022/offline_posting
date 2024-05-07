import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def get_updates_user_count(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    
    # Initialize a dictionary to store the count of customers
    counts = {
        "users_count": 0
    }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_user = f'[["User","{server}","=","1"]]'
            
            # Define URLs for API requests
            url_users = f"https://erp.metrogroupng.com/api/resource/User?fields=[%22name%22]&filters={filters_user}"
    
            # Make the API request
            try:
                response_users = requests.get(url_users, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_users.status_code == 200:
                    try:
          
                        users = set()

                            
                        for user in response_users.json().get('data', []):
                            users.add(user.get('name'))
        
                        counts = {
                  
                            "users_count": len(users),
                            
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
