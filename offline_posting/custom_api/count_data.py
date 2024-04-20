import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from datetime import timedelta
import json
import requests

@frappe.whitelist()
def get_updates_item_count(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url_item_prices = "https://erp.metrogroupng.com/api/resource/Item%20Price?fields=[%22name%22,%22item_code%22,%22price_list%22,%22price_list_rate%22]&filters=[[%22Item%20Price%22,%22price_list%22,%22=%22,%22Standard%20Selling%22],[%22Item%20Price%22,%22custom_update%22,%22=%22,%221%22]]"
    url_customers = "https://erp.metrogroupng.com/api/resource/Customer?fields=[%22name%22,%22customer_name%22,%22customer_type%22,%22customer_group%22,%22territory%22]&filters=[[%22Customer%22,%22custom_update%22,%22=%22,%221%22]]"
    url_item = "https://erp.metrogroupng.com/api/resource/Item?filters=%7B%22custom_post%22%3A1%2C%22custom_return_code%22%3A%22%22%7D&fields=%5B%22name%22%2C%22item_name%22%2C%22item_group%22%5D"
    url_stock_transfer = "https://erp.metrogroupng.com/api/resource/Stock%20Entry?filters={%22docstatus%22:1,%22custom_post%22:1,%22stock_entry_type%22:%22Material%20Transfer%22}&fields=[%22name%22,%22from_warehouse%22,%22to_warehouse%22,%22company%22,%22posting_date%22,%22stock_entry_type%22,%22items.item_code%22,%22items.qty%22,%22items.basic_rate%22]"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response_customers = requests.get(url_customers, headers=headers)
    response_item_price = requests.get(url_item_prices, headers=headers)
    response_item = requests.get(url_item, headers=headers)
    response_stock_transfer = requests.get(url_stock_transfer, headers=headers)

    if response_customers.status_code == 200 and response_item_price.status_code == 200 and response_item.status_code == 200 and response_stock_transfer.status_code == 200:
        try:
            customers = set()
            items_price = set()
            items = set()
            stock_transfer = set()

            for customer in response_customers.json().get('data', []):
                customers.add(customer.get('name'))

            for item_price in response_item_price.json().get('data', []):
                items_price.add(item_price.get('name'))

            for item in response_item.json().get('data', []):
                items.add(item.get('name'))

            for transfer in response_stock_transfer.json().get('data', []):
                stock_transfer.add(transfer.get('name'))

            return {
                "customers_count": len(customers),
                "stock_transfer_count": len(stock_transfer),
                "items_price_count": len(items_price),
                "items_count": len(items)
            }
        except json.decoder.JSONDecodeError as e:
            return {"error": f"Failed to decode JSON: {e}"}
    else:
        return {"error": f"Failed to fetch data. Customers Status Code: {response_customers.status_code}, Items Status Code: {response_item_price.status_code}"}
