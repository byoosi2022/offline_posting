import json
import requests
import frappe
from offline_posting.utils import get_api_keys12

def get_customer(docname, headers):
    try:
        response = requests.get(f"https://erp.metrogroupng.com/api/resource/Customer/{docname}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return None  # Customer does not exist
        frappe.log_error(f"HTTP error occurred: {http_err}")
        raise
    except Exception as err:
        frappe.log_error(f"Other error occurred: {err}")
        raise

@frappe.whitelist()
def create_or_update_customer(docname):
    try:
        api_keys = get_api_keys12()
        if not api_keys or not api_keys[0]:
            frappe.msgprint("Failed to get API keys for the server")
            return

        customer_doc = frappe.get_doc("Customer", docname)

        post_data = {
            "customer_name": customer_doc.customer_name,
            "customer_type": customer_doc.customer_type,
            "territory": customer_doc.territory,
            "customer_group": customer_doc.customer_group,
            "custom_company": customer_doc.custom_company,
            "custom_house_number": customer_doc.custom_house_number
        }

        json_data = json.dumps(post_data)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {api_keys[0][0]}:{api_keys[0][1]}"
        }
        server = "https://erp.metrogroupng.com/api/resource"

        # Check if the customer exists
        existing_customer = get_customer(docname, headers)

        if existing_customer:
            # Customer exists, update it
            put_response = requests.put(f"{server}/Customer/{docname}", headers=headers, data=json_data)
            put_response.raise_for_status()
            frappe.msgprint(f"Customer '{docname}' updated successfully.")
        else:
            # Customer does not exist, create it
            post_response = requests.post(f"{server}/Customer", headers=headers, data=json_data)
            post_response.raise_for_status()
            frappe.msgprint("Customer created successfully")
    except requests.exceptions.HTTPError as http_err:
        frappe.log_error(f"HTTP error occurred: {http_err}")
        frappe.throw(f"Failed to fetch or process data: {http_err}")
    except Exception as err:
        frappe.log_error(f"Other error occurred: {err}")
        frappe.throw(f"Failed to fetch or process data: {err}")
