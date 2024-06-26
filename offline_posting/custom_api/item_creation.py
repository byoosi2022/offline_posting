import requests
import frappe # type: ignore
from frappe.utils.background_jobs import enqueue 
import json
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server

@frappe.whitelist()
def get_updates_item(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    for server, value in response_server.items():
        if value == 1:
            filters_item = f'[["Item","{server}","=","1"]]'
            fields = '%5B%22name%22%2C%22item_name%22%2C%22item_group%22%2C%22item_code%22%2C%22custom_company%22%2C%22stock_uom%22%2C%22is_stock_item%22%2C%22valuation_rate%22%5D'
            url = f"https://erp.metrogroupng.com/api/resource/Item?fields={fields}&filters={filters_item}"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"token {api_key}:{secret_key}"
            }

            response = requests.get(url, headers=headers)
           
            if response.status_code == 200:
                try:
                    res = response.json()
                    for item_data in res.get('data', []):
                            update_or_create_item(item_data, server)
                except json.decoder.JSONDecodeError as e:
                    frappe.msgprint(f"Failed to decode JSON: {e}")
            else:
                frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")

def update_or_create_item(item_data, server):
    item_code = item_data.get('item_code')
    if not frappe.db.exists('Item', item_code):
        create_item(item_data)
    else:
        update_item(item_code, item_data, server)
        
@frappe.whitelist()
def create_item(item_data):
    item = frappe.new_doc('Item')
    set_item_data(item, item_data)
    item.insert()
    frappe.msgprint(f"Item '{item.item_code}' created successfully.")

def update_item(item_code, item_data, server):
    item = frappe.get_doc('Item', item_code)
    if item:
        set_item_data(item, item_data)
        item.save()
        frappe.msgprint(f"Item '{item.item_code}' updated successfully.")
        uncheck_custom_update(item_code, server)
    else:
        frappe.msgprint(f"Item '{item.item_code}' not found in ERPNext.")

def set_item_data(item, item_data):
    item.item_name = item_data.get('item_name', '')
    item.item_code = item_data.get('item_code', '')
    item.item_group = item_data.get('item_group', '')
    item.custom_company = item_data.get('custom_company', '')
    item.valuation_rate = item_data.get('valuation_rate', 2000)

def uncheck_custom_update(item_code, server):
    api_key, secret_key = get_api_keys()
    patch_url = f"https://erp.metrogroupng.com/api/resource/Item/{item_code}"
    patch_data = {
        "custom_update": 0,
        f"{server}": 0
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }
    patch_response = requests.put(patch_url, headers=headers, json=patch_data)
    if patch_response.status_code == 200:
        frappe.msgprint(f"Custom update field unchecked for '{item_code}'.")
    else:
        frappe.msgprint(f"Failed to uncheck custom update field for '{item_code}'. Status Code: {patch_response.status_code}")

def check_internet_item():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # frappe.log_error(f"Internet Available from Remote From ITEM ")
        get_updates_item()
        
    except requests.RequestException:
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()
         
# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.item_creation.check_internet_item", queue='short')
# Assuming this code is running in a background job, so we don't need to enqueue it
check_internet_item()
