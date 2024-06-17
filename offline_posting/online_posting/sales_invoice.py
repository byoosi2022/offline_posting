import json
import requests
import frappe
from datetime import datetime
from offline_posting.utils import get_api_keys  # Import the function to fetch API keys

@frappe.whitelist()
def post_sales_invoices(doc,method=None):
    try:
        api_keys = get_api_keys()  
        if not api_keys or not api_keys[0]:
            frappe.msgprint("Failed to get API keys for the server")
            return

        sales_invoice = frappe.get_doc("Sales Invoice", doc)
        # Check if the Sales Invoice has already been posted
        if sales_invoice.custom_voucher_no:
            frappe.msgprint("Sales Invoice has already been posted.")
            return

        # Convert date fields to strings
        sales_invoice.posting_date = datetime.strftime(sales_invoice.posting_date, "%Y-%m-%d")

        # Convert items to a list of dictionaries
        items = []
        for item in sales_invoice.items:
            item_dict = {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate,
                "warehouse": item.warehouse
            }
            items.append(item_dict)

        post_data = {
            "customer": sales_invoice.customer,
            "posting_date": sales_invoice.posting_date,
            "posting_time": str(sales_invoice.posting_time),
            "company": sales_invoice.company,
            # "docstatus": 0,
            "custom_voucher_no": sales_invoice.name,
            "items": items
        }

        json_data = json.dumps(post_data)

        # Make the request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {api_keys[0][0]}:{api_keys[0][1]}"
        }
        server = "https://erp.metrogroupng.com/api/resource"

        # Ensure the customer exists
        ensure_customer_exists(sales_invoice.customer, headers, server)

        # Ensure each item exists
        for item in items:
            ensure_item_exists(item["item_code"], headers, server)

        # Remove the 'Expect' header
        headers.pop('Expect', None)

        post_response = requests.post(f"{server}/Sales%20Invoice", headers=headers, data=json_data)

        # Check the response
        post_response.raise_for_status()
        posted_invoice = post_response.json().get("data", {}).get("name")

        # Update the document status
        if posted_invoice:
            frappe.db.set_value("Sales Invoice", sales_invoice.name, "custom_voucher_no", posted_invoice)
            frappe.db.set_value("Sales Invoice", sales_invoice.name, "custom_post_status", "Invoice Posted")
            frappe.msgprint("Sales Invoice submitted successfully to the server")
        else:
            frappe.db.set_value("Sales Invoice", sales_invoice.name, "custom_post_status", "Invoice Not Posted")
            frappe.msgprint("Failed to post Sales Invoice")

    except requests.exceptions.HTTPError as http_err:
        frappe.log_error(f"HTTP error occurred: {http_err}")
        frappe.throw(f"Failed to fetch or process data: {http_err}")
    except Exception as err:
        frappe.log_error(f"Other error occurred: {err}")
        frappe.throw(f"Failed to fetch or process data: {err}")

def ensure_customer_exists(customer, headers, server):
    try:
        response = requests.get(f"{server}/Customer/{customer}", headers=headers)
        if response.status_code == 404:
            customer_data = {
                "doctype": "Customer",
                "customer_name": customer,
                "customer_type": "Company",  # Modify this as per your requirements
                "customer_group": "All Customer Groups"  # Example field
            }
            response = requests.post(f"{server}/Customer", headers=headers, data=json.dumps(customer_data))
            response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        frappe.log_error(f"HTTP error occurred: {http_err}")
        raise
    except Exception as err:
        frappe.log_error(f"Other error occurred: {err}")
        raise
    
def ensure_item_exists(item_code, headers, server):
    try:
        response = requests.get(f"{server}/Item/{item_code}", headers=headers)
        if response.status_code == 404:
            item_data = {
                "doctype": "Item",
                "item_code": item_code,
                # Add other fields as needed
            }
            response = requests.post(f"{server}/Item", headers=headers, data=json.dumps(item_data))
            response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        frappe.log_error(f"HTTP error occurred: {http_err}")
        raise
    except Exception as err:
        frappe.log_error(f"Other error occurred: {err}")
        raise

