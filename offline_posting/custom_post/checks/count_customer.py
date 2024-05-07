import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def get_updates_customer_count(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    
    # Initialize a dictionary to store the count of customers
    counts = {
        "customers_count": 0

    }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_customer = f'[["Customer","{server}","=","1"]]'
            
            # Define URLs for API requests
            url_customers = f"https://erp.metrogroupng.com/api/resource/Customer?fields=[%22name%22]&filters={filters_customer}"
          
            # Make the API request
            try:
                response_customers = requests.get(url_customers, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_customers.status_code == 200:
                    try:
                        customers = set()
                        for customer in response_customers.json().get('data', []):
                            customers.add(customer.get('name'))
                            
                        counts = {
                            "customers_count": len(customers),
                                              
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
