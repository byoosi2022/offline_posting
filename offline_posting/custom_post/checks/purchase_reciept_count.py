import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def get_updates_reciept_count(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    
    # Initialize a dictionary to store the count of customers
    counts = {
        
        "receipts_count": 0,
       
    }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_receipt = f'[["Purchase Receipt","{server}","=","1"],["Purchase Receipt","docstatus","=","1"],["Purchase Receipt","custom_voucher_no","=",""]]'
   
            
            # Define URLs for API requests
            url_receipts = f"https://erp.metrogroupng.com/api/resource/Purchase%20Receipt?fields=[%22name%22]&filters={filters_receipt}"
           
            # Make the API request
            try:
                response_receipts = requests.get(url_receipts, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_receipts.status_code == 200:
                    try:
                  
                        receipts = set()
               
                            
                        for reciept in response_receipts.json().get('data', []):
                            receipts.add(reciept.get('name'))

                        counts = {
            
                            "receipts_count": len(receipts),
          
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
