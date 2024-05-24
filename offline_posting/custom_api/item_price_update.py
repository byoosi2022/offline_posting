from venv import logger
import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
from datetime import timedelta
import json
import requests
import logging

@frappe.whitelist()
def get_updates_item_prices(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    response_server = local_server()

    for server, value in response_server.items():
        if value == 1:
            filters_item_prices = f'[["Item Price","price_list","=","Standard Selling"],["Item Price","{server}","=","1"]]'
            url = f"https://erp.metrogroupng.com/api/resource/Item%20Price?fields=[%22name%22,%22item_code%22,%22price_list%22,%22price_list_rate%22,%22uom%22]&filters={filters_item_prices}"

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
                            # Check if item exists, if not, create it
                            if not frappe.db.exists("Item", item_code):
                                new_item = frappe.new_doc("Item")
                                new_item.item_code = item_code
                                new_item.item_name = item_code
                                new_item.item_group = "All Item Groups"  # Modify this as necessary
                                new_item.stock_uom = item_price_data.get('uom') or "Nos"  # Default to 'Nos' if UOM is not provided
                                new_item.valuation_rate = 2000  # Assign default valuation_rate here
                                new_item.insert()
                                frappe.msgprint(f"Item '{item_code}' created successfully.")

                            item_prices = frappe.get_all("Item Price", filters={"item_code": item_code, "price_list": "Standard Selling"})
                            if not item_prices:  # Create item price if it doesn't exist
                                new_item_price = frappe.new_doc("Item Price")
                                new_item_price.item_code = item_code
                                new_item_price.price_list = "Standard Selling"
                                new_item_price.price_list_rate = item_price_data.get('price_list_rate')
                                new_item_price.uom = item_price_data.get('uom')
                                new_item_price.save()
                                frappe.msgprint(f"Item Price '{item_code}' created successfully.")

                            for item_price in item_prices:
                                item = frappe.get_doc('Item Price', item_price["name"])
                                if item:
                                    item.price_list_rate = item_price_data.get('price_list_rate')
                                    item.uom = item_price_data.get('uom')
                                    # item.valuation_rate = item_price_data.get('valuation_rate', 2000)
                                    item.save()
                                    frappe.msgprint(f"Item Price '{item_code}' updated successfully.")

                                    # Uncheck the custom_update field
                                    patch_url = f"https://erp.metrogroupng.com/api/resource/Item Price/{item_price_data.get('name')}"
                                    patch_data = {
                                        "custom_update": 0,
                                        f"{server}": 0
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
                frappe.msgprint(f"Failed to fetch data for server '{server}'. Status Code: {response.status_code}")

# Define a function to check internet connection for item_price_update
def check_internet_item_price_update():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        # frappe.log_error(f"Internet Available from Remote From item_price_update ")
        get_updates_item_prices()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()
        # frappe.log_error(f"No Internet Available from Remote From item_price_update ")

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.item_price_update.check_internet_item_price_update", queue='short')

# Start the check_internet loop
check_internet_item_price_update()
