import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def get_updates_item_price_count(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    
    # Initialize a dictionary to store the count of customers
    counts = {
    
        "item_prices_count": 0,
   
    }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_item_prices = f'[["Item Price","price_list","=","Standard Selling"],["Item Price","{server}","=","1"]]'
             
            # Define URLs for API requests
            url_item_prices = f"https://erp.metrogroupng.com/api/resource/Item%20Price?fields=[%22name%22]&filters={filters_item_prices}"
           
            # Make the API request
            try:
                response_item_prices = requests.get(url_item_prices, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_item_prices.status_code == 200:
                    try:
           
                        item_prices = set()
            

                        for item_price in response_item_prices.json().get('data', []):
                            item_prices.add(item_price.get('name'))


                        counts = {
                    
                            "item_prices_count": len(item_prices),
                  
                            
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
