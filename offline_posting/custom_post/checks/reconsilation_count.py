import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def get_stock_reconciliation_count(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    
    # Initialize a dictionary to store the count of customers
    counts = {
        "stock_reconciliation_count": 0,
      }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
            filters_reconciliation = f'[["Stock Reconciliation","docstatus","=","1"],["Stock Reconciliation","{server}","=","1"]]'
            url_reconciliation = f"https://erp.metrogroupng.com/api/resource/Stock%20Reconciliation?filters={filters_reconciliation}&fields=[%22name%22,%22posting_date%22,%22posting_time%22,%22company%22,%22items.item_code%22,%22items.qty%22,%22items.valuation_rate%22,%22purpose%22,%22set_warehouse%22,%22expense_account%22]&limit_page_length=1000"
                
            # Make the API request
            try:
                response_stock_reconciliation  = requests.get(url_reconciliation, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_stock_reconciliation.status_code == 200:
                    try:
                  
                        stock_reconciliation = set()
     
                        for stock_transfer in response_stock_reconciliation.json().get('data', []):
                            stock_reconciliation.add(stock_transfer.get('name'))


                        counts = {
                  
                            "stock_reconciliation_count": len(stock_reconciliation),
                        
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
