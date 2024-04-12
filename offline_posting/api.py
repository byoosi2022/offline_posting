import json
import requests
import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys

@frappe.whitelist()
def post_item(doc=None,method=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Item"
    headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {api_key}:{secret_key}"
        }

    data = {
            "data": {
                "item_code": doc['name'],
                "item_name": doc['item_name'],
                "item_group": doc['item_group']
            }
        }

    try:       
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        # if success update the custom_return_code with 00
        frappe.db.set_value("Item", doc['name'], "custom_return_code", "00")
        frappe.db.commit()
        frappe.log_error(f"Item {doc['name']} posted successfully in the other ERPNext system.")
    except Exception as e:
            frappe.log_error(f"Failed to post item {doc['name']}: Request error - {e}")

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.api.check_internet", queue='long')

def check_internet():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        frappe.msgprint("Internet available, posting saved documents")
        post_saved_documents()
    except requests.ConnectionError:
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()
        frappe.msgprint("No internet connection")

def post_saved_documents():
    unsynced_docs = frappe.get_list("Item", filters={
        "custom_post": 1, 
        "custom_return_code": ""
        }, fields=[
            "name", 
            "item_name", 
            "item_group"
            ])
    for doc in unsynced_docs:
        post_item(doc)

check_internet()  # Start the check_internet loop
