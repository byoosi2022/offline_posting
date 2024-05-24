import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def post_supplier(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    live_suppliers = set(fetch_live_supplier_names(api_key, secret_key))
    local_suppliers = frappe.get_all("Supplier", filters={"custom_post": 1}, fields=["name", "supplier_name", "supplier_type", "country","supplier_group", "custom_company"])

    url = "https://erp.metrogroupng.com/api/resource/Supplier"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    for local_supplier in local_suppliers:
        if local_supplier['name'] in live_suppliers:
            # Updated if it exists
            patch_url = f"https://erp.metrogroupng.com/api/resource/Supplier/{local_supplier['name']}"
            patch_data = {
                "supplier_name": local_supplier['supplier_name'],
                "supplier_type": local_supplier['supplier_type'],
                "custom_company": local_supplier['custom_company'],
                "country": local_supplier['country'],
                "supplier_group": local_supplier['supplier_group']
            }
            # Check if response_server is available and update the corresponding field
            response_server = local_server()
            if response_server:
                for server, value in response_server.items():
                    if value == 1:
                        patch_data[server] = 0
                    else:
                        patch_data[server] = 1
            
            patch_response = requests.put(patch_url, headers=headers, json=patch_data)
            if patch_response.status_code == 200:
                frappe.db.set_value("Supplier", local_supplier['name'], "custom_post", 0)
                frappe.db.commit()
                frappe.log_error(f"Supplier {local_supplier['name']} posted successfully in the other System.")
                frappe.msgprint(f"Custom update field unchecked for '{local_supplier['name']}'.")
            else:
                frappe.msgprint(f"Failed to uncheck custom update field for '{local_supplier['name']}'. Status Code: {patch_response.status_code}")
       
            frappe.msgprint(f"Supplier <a href='https://erp.metrogroupng.com/app/supplier/{local_supplier['name']}'>{local_supplier['name']}</a> already exists in live site ")
            continue

        data = {
            "supplier_name": local_supplier['supplier_name'],
            "supplier_type": local_supplier['supplier_type'],
            "country": local_supplier['country'],
            "custom_company": local_supplier['custom_company'],
            "supplier_group": local_supplier['supplier_group']
        }
        # Check if response_server is available and update the corresponding field
        response_server = local_server()
        if response_server:
            for server, value in response_server.items():
                if value == 1:
                    data[server] = 0
                else:
                    data[server] = 1

        response = requests.post(url, json=data, headers=headers)

        try:
            res = response.json()
            if res.get('status') == 'ok':
                frappe.db.set_value("Supplier", local_supplier['name'], "custom_post", 0)
                frappe.db.commit()
                frappe.log_error(f"Supplier {local_supplier['name']} posted successfully in the other System.")
                frappe.msgprint("Data posted successfully")
            else:
                print("Failed to post data")
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")


def fetch_live_supplier_names(api_key, secret_key):
    url = "https://erp.metrogroupng.com/api/method/metro_custom_app.api.get_all_suppliers"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        try:
            res = response.json()
            if 'message' in res and 'data' in res['message']:
                suppliers = res['message']['data']
                if isinstance(suppliers, list):
                    return [supplier["name"] for supplier in suppliers]
                else:
                    frappe.msgprint(f"Invalid data format received: {type(suppliers)}")
                    return []
            else:
                frappe.msgprint("Invalid data format received: 'message' or 'data' key not found in response")
                return []
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
            return []
    else:
        frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")
        return []
    
# Define a function to check internet connection for customer
def check_internet_supplier():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        post_supplier()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_post.supplier_post.check_internet_supplier", queue='short')

# Start the check_internet loop
check_internet_supplier()
