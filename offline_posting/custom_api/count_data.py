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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response_customers = requests.get(url_customers, headers=headers)
    response_items = requests.get(url_item_prices, headers=headers)

    if response_customers.status_code == 200 and response_items.status_code == 200:
        try:
            customers_count = len(response_customers.json().get('data', []))
            items_count = len(response_items.json().get('data', []))
            return {"customers_count": customers_count, "items_count": items_count}
        except json.decoder.JSONDecodeError as e:
            return {"error": f"Failed to decode JSON: {e}"}
    else:
        return {"error": f"Failed to fetch data. Customers Status Code: {response_customers.status_code}, Items Status Code: {response_items.status_code}"}
