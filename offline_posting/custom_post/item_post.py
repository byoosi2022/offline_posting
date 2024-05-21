from venv import logger
import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests
import logging

@frappe.whitelist()
def post_item(doc=None, method=None, schedule_at=None):
    # Get API keys
    api_key, secret_key = get_api_keys()
    # Get response from local server
    response_server = local_server()
    # Get list of local items to be posted
    local_items = frappe.db.get_list(
        "Item",
        filters={"custom_post": 1},
        fields=["name", "item_name", "item_group", "item_code", "custom_company","valuation_rate"]
    )

    url = "https://erp.metrogroupng.com/api/resource/Item"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    for local_item in local_items:
        item_code = local_item.get("name")
        check_url = f"https://erp.metrogroupng.com/api/method/metro_custom_app.api.get_all_items_filters?item_code={item_code}"
        try:
            check_response = requests.get(check_url, headers=headers)
            check_response.raise_for_status()
            remote_items = check_response.json().get("message").get("data", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check item '{item_code}' existence: {e}")
            continue

        if not remote_items:
            # Item does not exist remotely, create it
            data = {
                "item_name": local_item['item_name'],
                "item_group": local_item['item_group'],
                "item_code": local_item['item_code'],
                "custom_company": local_item['custom_company'],
                "valuation_rate": local_item['valuation_rate']
               
            }
            # Check if response_server is available and update the corresponding field
            for server, value in response_server.items():
                if value == 1:
                    data[server] = 0
                else:
                    data[server] = 1

            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                frappe.db.set_value("Item", item_code, "custom_post", 0)
                frappe.db.commit()
                frappe.msgprint(f"Item '{local_item['item_code']}' created successfully.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to create item '{item_code}': {e}")
            continue

        # Item exists remotely, check for changes
        remote_item = remote_items[0]
        if any(local_item[field] != remote_item.get(field) for field in ["item_name", "item_group", "item_code", "custom_company","valuation_rate"]):
            # Item has changes, update it
            patch_url = f"https://erp.metrogroupng.com/api/resource/Item/{item_code}"
            patch_data = {
                "item_name": local_item['item_name'],
                "item_group": local_item['item_group'],
                "item_code": local_item['item_code'],
                "valuation_rate": local_item['valuation_rate'],
                "custom_company": local_item['custom_company']
            }
            # Check if response_server is available and update the corresponding field
            for server, value in response_server.items():
                if value == 1:
                    patch_data[server] = 0
                else:
                    patch_data[server] = 1

            try:
                response = requests.put(patch_url, json=patch_data, headers=headers)
                response.raise_for_status()
                frappe.db.set_value("Item", item_code, "custom_post", 0)
                frappe.db.commit()
                frappe.msgprint(f"Item '{item_code}' updated successfully.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to update item '{item_code}': {e}")
        else:
            logger.info(f"No changes for item '{item_code}'. Skipping...")
            
# Define a function to check internet connection for customer
def check_internet_item():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # frappe.log_error(f"Internet Availabe")
        # Internet connection is available, so we can attempt to post saved documents
        post_item()
    except requests.RequestException:
        # No internet connection, update the database
        # frappe.log_error(f"Not Internet Availabe")
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule the job to run
enqueue("offline_posting.custom_post.item_post.check_internet_item", queue='long')
# Start the check_internet loop
check_internet_item()
