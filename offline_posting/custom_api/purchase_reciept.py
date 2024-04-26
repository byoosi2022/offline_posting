import requests
import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from datetime import timedelta
import json

@frappe.whitelist()
def post_saved_documents(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Sales Invoice"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    unsynced_docs = frappe.db.get_all("Sales Invoice", filters={
        "custom_post": 1,
        "docstatus":1,
        "custom_return_code": ""
    }, fields=["name", "paid_amount", "update_stock", "posting_date", "customer", "company", "is_pos", "docstatus", "pos_profile"])

    if not unsynced_docs:
        return

    for doc in unsynced_docs:
        invoice_name = doc.get("name")

        items = frappe.get_all("Sales Invoice Item", filters={"parent": invoice_name},
                               fields=["item_code", "qty", "rate"])
        payments = frappe.get_all("Sales Invoice Payment", filters={"parent": invoice_name},
                                  fields=["amount", "mode_of_payment", "base_amount", "account"])

        try:
            customer = doc.get("customer")
            if not customer or not items:
                raise ValueError("Customer or Items field is empty")

            item_list = []
            for item in items:
                item_data = {
                    "item_code": item.get("item_code"),
                    "qty": item.get("qty"),
                    "rate": item.get("rate")
                }
                item_list.append(item_data)

            payment_list = []
            for payment in payments:
                payment_data = {
                    "amount": payment.get("amount"),
                    "mode_of_payment": payment.get("mode_of_payment"),
                    "base_amount": payment.get("amount"),
                    "account": payment.get("account")
                }
                payment_list.append(payment_data)

            # Calculate outstanding amount
            total_amount = sum(item.get("rate") * item.get("qty") for item in items)
            paid_amount = doc.get("paid_amount", 0.00)
            outstanding_amount = max(total_amount - paid_amount, 0.00)

            data = {
                "data": {
                    "customer": customer,
                    "pos_profile": doc.get("pos_profile"),
                    "paid_amount": doc.get("paid_amount"),
                    "update_stock": doc.get("update_stock"),
                    "company": doc.get("company"),
                    "is_pos": 1,
                    "docstatus": doc.get("docstatus"),
                    "items": item_list,
                    "payments": payment_list
                }
            }
            response = requests.post(url, json=data, headers=headers)
            
            response.raise_for_status()
            res = response.json()
            res_json = json.dumps(res)
            name = res["data"]["name"]
            frappe.db.set_value("Sales Invoice", doc["name"], "custom_return_code", "Data Posted")
            frappe.db.set_value("Sales Invoice", doc["name"], "custom_voucher_no", res["data"]["name"])
            frappe.db.commit()
            frappe.log_error(f"SI {doc['name']} posted successfully in the other PURCHASE RECIEPT.")
            
                 # Uncheck the custom_post field
            patch_url = f"https://erp.metrogroupng.com/api/resource/Sales Invoice/{name}"
            patch_data = {"custom_voucher_no": invoice_name}
            requests.put(patch_url, headers=headers, json=patch_data)
            
            # Optionally, you can enqueue a background job to process the document
            enqueue("offline_posting.custom_api.purchase_reciept.process_document", queue='long')
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
enqueue("offline_posting.custom_api.purchase_reciept.check_internet", queue='long')

# Start the check_internet loop
check_internet()
