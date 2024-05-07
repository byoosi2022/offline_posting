import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def get_updates_item_count(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    
    # Initialize a dictionary to store the count of customers
    counts = {
        "items_count": 0,
          }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_item = f'[["Item","{server}","=","1"]]'
            
            # Define URLs for API requests
            url_items = f"https://erp.metrogroupng.com/api/resource/Item?fields=[%22name%22]&filters={filters_item}"
            
            # Make the API request
            try:
                response_items = requests.get(url_items, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_items.status_code == 200:
                    try:
                        items = set()
             

                            
                        for item in response_items.json().get('data', []):
                            items.add(item.get('name'))
           
                        counts = {
             
                            "items_count": len(items),
                  
                            
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
