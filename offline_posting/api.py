import requests
import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
import json

def post_saved_documents(doc=None, method=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Item"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }
    unsynced_docs = frappe.db.get_all("Item", filters={
        "custom_post": 1,
        "custom_return_code": ""
    }, fields=["name", "item_name", "item_group"])

    for doc in unsynced_docs:
        data = {
            "data": {
                "item_code": doc.get("name"),
                "item_name": doc.get("item_name"),
                "item_group": doc.get("item_group")
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            res = response.json()
            res_json = json.dumps(res)
            frappe.db.set_value("Item", doc["name"], "custom_return_code", "Data Posted")
            frappe.db.set_value("Item", doc["name"], "custom_main_content", res["data"]["name"])
            frappe.db.commit()
            frappe.log_error(f"Item {doc['name']} posted successfully in the other ERPNext system.")

            # Optionally, you can enqueue a background job to process the document
            enqueue("offline_posting.api.process_document", queue='long')
        except (ValueError, requests.RequestException) as e:
            # Log the error
            frappe.log_error(f"Failed to post item {doc['name']}: {e}")

            # Extract errors from the response, if available
            try:
                errors = response.json().get("data", {}).get("errors")
                frappe.log_error(f"Errors encountered: {errors}")
            except KeyError:
                pass  # No errors found in the response

            break

# Define a function to check internet connection
def check_internet():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        post_saved_documents()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.api.check_internet", queue='long')

# Start the check_internet loop
check_internet()
