import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def get_updates_supplier_count(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    
    # Initialize a dictionary to store the count of customers
    counts = {
          "suppliers_count": 0
      }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_supplier = f'[["Supplier","{server}","=","1"]]'
              
            # Define URLs for API requests
            url_suppliers = f"https://erp.metrogroupng.com/api/resource/Supplier?fields=[%22name%22]&filters={filters_supplier}"
           
            # Make the API request
            try:
                response_suppliers = requests.get(url_suppliers, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_suppliers.status_code == 200:
                    try:
                        suppliers = set()
                                     
                        for supplier in response_suppliers.json().get('data', []):
                            suppliers.add(supplier.get('name'))
                            
                        
                        counts = {
                                                 "supplier_count": len(suppliers),
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
