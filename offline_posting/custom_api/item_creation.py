import requests
import frappe
from offline_posting.utils import get_api_keys
import json
from frappe.utils.background_jobs import enqueue

@frappe.whitelist()
def get_updates_item(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Item?filters=%7B%22custom_post%22%3A1%7D&fields=%5B%22name%22%2C%22item_name%22%2C%22item_group%22%2C%22item_code%22%2C%22custom_company%22%5D"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            res = response.json()
            for item_data in res.get('data', []):
                item_code = item_data.get('item_code')
                custom_company = item_data.get('custom_company')
                if item_code:
                    if not frappe.db.exists('Item', item_code):
                        item = frappe.new_doc('Item')
                        item.item_code = item_code
                        item.item_name = item_data.get('item_name', '')
                        item.item_group = item_data.get('item_group', '')
                        item.custom_company = custom_company  # Assign the custom_company field
                        item.insert()
                        frappe.msgprint(f"Item '{item_code}' created successfully.")
                    else:
                        item = frappe.get_doc('Item', item_code)
                        if item:
                            item.item_name = item_data.get('item_name', '')
                            item.item_group = item_data.get('item_group', '')
                            item.custom_company = custom_company  # Assign the custom_company field
                            item.save()
                            frappe.msgprint(f"Item '{item_code}' updated successfully.")
                            # Uncheck the custom_update field
                            patch_url = f"https://erp.metrogroupng.com/api/resource/Item/{item_code}"
                            patch_data = {
                                "custom_post": 0
                            }
                            patch_response = requests.put(patch_url, headers=headers, json=patch_data)
                            if patch_response.status_code == 200:
                                frappe.msgprint(f"Custom update field unchecked for '{item_code}'.")
                            else:
                                frappe.msgprint(f"Failed to uncheck custom update field for '{item_code}'. Status Code: {patch_response.status_code}")
                        else:
                            frappe.msgprint(f"Item '{item_code}' not found in ERPNext.")
                else:
                    frappe.msgprint("Skipping item creation: item_code not provided.")
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
    else:
        frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")
        

# Define a function to check internet connection
def check_internet():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        get_updates_item()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.item_creation.check_internet", queue='long')

# Start the check_internet loop
check_internet()
