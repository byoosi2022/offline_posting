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
        "stock_transfers_count": 0,
      }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_stock_transfer = f'[["Stock Entry","{server}","=","1"],["Stock Entry","stock_entry_type","=","Material Transfer"],["Stock Entry","docstatus","=","1"],["Stock Entry","custom_voucher_no","=",""]]'
             
            # Define URLs for API requests
            url_stock_transfers = f"https://erp.metrogroupng.com/api/resource/Stock%20Entry?fields=[%22name%22]&filters={filters_stock_transfer}"
            
            # Make the API request
            try:
                response_stock_transfers = requests.get(url_stock_transfers, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_stock_transfers.status_code == 200:
                    try:
                  
                        stock_transfers = set()
     
                        for stock_transfer in response_stock_transfers.json().get('data', []):
                            stock_transfers.add(stock_transfer.get('name'))


                        counts = {
                  
                            "stock_transfers_count": len(stock_transfers),
                        
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
