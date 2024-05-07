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
        "customers_count": 0,
        "suppliers_count": 0,
        "item_prices_count": 0,
        "items_count": 0,
        "stock_transfers_count": 0,
        "receipts_count": 0,
        "users_count": 0
    }
    
    # Check if response_server is available and update the corresponding field
    for server, value in response_server.items():
        if value == 1:
           # Build the filters based on the response_server
            filters_customer = f'[["Customer","{server}","=","1"]]'
            filters_supplier = f'[["Supplier","{server}","=","1"]]'
            filters_item_prices = f'[["Item Price","price_list","=","Standard Selling"],["Item Price","{server}","=","1"],["Item Price"]]'
            filters_item = f'[["Item","{server}","=","1"]]'
            filters_stock_transfer = f'[["Stock Entry","{server}","=","1"],["Stock Entry","stock_entry_type","=","Material Transfer"],["Stock Entry","docstatus","=","1"]]'
            filters_receipt = f'[["Purchase Receipt","{server}","=","1"],["Purchase Receipt","docstatus","=","1"]]'
            filters_user = f'[["User","{server}","=","1"]]'
            
            # Define URLs for API requests
            url_customers = f"https://erp.metrogroupng.com/api/resource/Customer?fields=[%22name%22]&filters={filters_customer}"
            url_suppliers = f"https://erp.metrogroupng.com/api/resource/Supplier?fields=[%22name%22]&filters={filters_supplier}"
            url_item_prices = f"https://erp.metrogroupng.com/api/resource/Item%20Price?fields=[%22name%22]&filters={filters_item_prices}"
            url_items = f"https://erp.metrogroupng.com/api/resource/Item?fields=[%22name%22]&filters={filters_item}"
            url_stock_transfers = f"https://erp.metrogroupng.com/api/resource/Stock%20Entry?fields=[%22name%22]&filters={filters_stock_transfer}"
            url_receipts = f"https://erp.metrogroupng.com/api/resource/Purchase%20Receipt?fields=[%22name%22]&filters={filters_receipt}"
            url_users = f"https://erp.metrogroupng.com/api/resource/User?fields=[%22name%22]&filters={filters_user}"
    
            # Make the API request
            try:
                response_customers = requests.get(url_customers, headers={"Authorization": f"token {api_key}:{secret_key}"})
                response_suppliers = requests.get(url_suppliers, headers={"Authorization": f"token {api_key}:{secret_key}"})
                response_item_prices = requests.get(url_item_prices, headers={"Authorization": f"token {api_key}:{secret_key}"})
                response_items = requests.get(url_items, headers={"Authorization": f"token {api_key}:{secret_key}"})
                response_stock_transfers = requests.get(url_stock_transfers, headers={"Authorization": f"token {api_key}:{secret_key}"})
                response_receipts = requests.get(url_receipts, headers={"Authorization": f"token {api_key}:{secret_key}"})
                response_users = requests.get(url_users, headers={"Authorization": f"token {api_key}:{secret_key}"})
                if response_item_prices.status_code == 200 and response_items.status_code == 200 and response_stock_transfers.status_code == 200 and response_receipts.status_code == 200 and response_users.status_code == 200 and response_customers.status_code == 200 and response_suppliers.status_code == 200:
                    try:
                        customers = set()
                        suppliers = set()
                        item_prices = set()
                        items = set()
                        stock_transfers = set()
                        receipts = set()
                        users = set()

                        for customer in response_customers.json().get('data', []):
                            customers.add(customer.get('name'))
                            
                        for supplier in response_suppliers.json().get('data', []):
                            suppliers.add(supplier.get('name'))
                            
                        for item_price in response_item_prices.json().get('data', []):
                            item_prices.add(item_price.get('name'))
                            
                        for item in response_items.json().get('data', []):
                            items.add(item.get('name'))
                            
                        for stock_transfer in response_stock_transfers.json().get('data', []):
                            stock_transfers.add(stock_transfer.get('name'))
                            
                        for user in response_users.json().get('data', []):
                            users.add(user.get('name'))
                            
                        for reciept in response_receipts.json().get('data', []):
                            receipts.add(reciept.get('name'))

                        counts = {
                            "customers_count": len(customers),
                            "supplier_count": len(suppliers),
                            "item_prices_count": len(item_prices),
                            "items_count": len(items),
                            "stock_transfers_count": len(stock_transfers),
                            "receipts_count": len(receipts),
                            "users_count": len(users),
                            
                            }
                    except json.decoder.JSONDecodeError as e:
                        return {"error": f"Failed to decode JSON: {e}"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to fetch data for server {server}: {e}"}

    return counts
