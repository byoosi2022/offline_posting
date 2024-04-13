import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from datetime import timedelta
import json
import requests

@frappe.whitelist()
def get_updates_item_prices(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Item%20Price?fields=[%22name%22,%22item_code%22,%22price_list%22,%22price_list_rate%22]&filters=[[%22Item%20Price%22,%22price_list%22,%22=%22,%22Standard%20Selling%22],[%22Item%20Price%22,%22custom_update%22,%22=%22,%221%22]]"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            res = response.json()
            for item_price_data in res.get('data', []):
                item_code = item_price_data.get('item_code')
                if item_code:
                    item_prices = frappe.get_all("Item Price", filters={"item_code": item_code, "price_list": "Standard Selling"})
                    for item_price in item_prices:
                        item = frappe.get_doc('Item Price', item_price["name"])
                        if item:
                            item.price_list_rate = item_price_data.get('price_list_rate')
                            item.save()
                            frappe.msgprint(f"Item Price '{item_code}' updated successfully.")
                            
                            # Uncheck the custom_update field
                            patch_url = f"https://erp.metrogroupng.com/api/resource/Item Price/{item_price_data.get('name')}"
                            patch_data = {
                                    "custom_update": 0
                            }
                            patch_response = requests.put(patch_url, headers=headers, json=patch_data)
                            if patch_response.status_code == 200:
                                frappe.msgprint(f"Custom update field unchecked for '{item_code}'.")
                            else:
                                frappe.msgprint(f"Failed to uncheck custom update field for '{item_code}'. Status Code: {patch_response.status_code}")
                        
                        else:
                            frappe.msgprint(f"Item Price '{item_code}' not found in ERPNext.")
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
    else:
        frappe.msgprint(f"Failed to fetch data. Status Code: {response.status_code}")
