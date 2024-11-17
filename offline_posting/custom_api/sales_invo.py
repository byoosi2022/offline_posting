import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from datetime import datetime, timedelta
import json
import requests

def check_stock_availability(items, headers):
    insufficient_stock_items = []
    for item in items:
        item_code = item.get("item_code")
        required_qty = item.get("qty")
        warehouse = item.get("warehouse")

        filters = [["item_code", "=", item_code], ["warehouse", "=", warehouse]]
        fields = ["item_code", "warehouse", "actual_qty"]

        response = requests.get("https://erp.metrogroupng.com/api/resource/Bin",
                                params={"filters": json.dumps(filters), "fields": json.dumps(fields)},
                                headers=headers)
        try:
            response.raise_for_status()
            data = response.json()

            if "data" not in data or not data["data"]:
                frappe.log_error(f"Unexpected response format or empty data for item {item_code} in warehouse {warehouse}: {json.dumps(data)}", "check_stock_availability")
                insufficient_stock_items.append({"item_code": item_code, "required_qty": required_qty, "available_qty": 0, "warehouse": warehouse})
                continue

            available_qty = sum(bin_entry.get("actual_qty", 0) for bin_entry in data["data"])

            if available_qty < required_qty:
                additional_qty_needed = required_qty - available_qty
                insufficient_stock_items.append({"item_code": item_code, "required_qty": required_qty, "available_qty": available_qty, "warehouse": warehouse})
                message = f"Insufficient stock for item {item_code} in warehouse {warehouse}. Available: {available_qty}, Needed: {required_qty}, Additional quantity required: {additional_qty_needed}"
                frappe.log_error(message, "check_stock_availability")
                frappe.msgprint(message)
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Error fetching stock data for item {item_code} in warehouse {warehouse}: {e}")
            insufficient_stock_items.append({"item_code": item_code, "required_qty": required_qty, "available_qty": 0, "warehouse": warehouse})

    return insufficient_stock_items

@frappe.whitelist()
def post_saved_documents(doc=None, method=None, schedule_at=None, posting_date=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Sales Invoice"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }
    current_user = frappe.session.user
    unsynced_docs = frappe.db.get_all("Sales Invoice", filters={
        "custom_post": 1,
        "docstatus": 1,
        "custom_return_code": "",
        "custom_post_as_draft": 1,
        "posting_date": posting_date,
        "custom_voucher_no": "",
        "owner": current_user  # Ensure only documents owned by the current user
    }, fields=["name", "paid_amount", "update_stock", "posting_date", "posting_time", "customer", "company", "is_pos", "docstatus", "pos_profile"])
    if not unsynced_docs:
        frappe.msgprint("No documents to post")
        return

    for doc in unsynced_docs:
        try:
            items = frappe.get_all("Sales Invoice Item", filters={"parent": doc["name"]},
                                    fields=["item_code", "qty", "rate", "warehouse"])
            payments = frappe.get_all("Sales Invoice Payment", filters={"parent": doc["name"]},
                                    fields=["amount", "mode_of_payment", "base_amount", "account"])

            if not items or not payments:
                raise ValueError("Items or Payments field is empty")

            item_list = []
            for item in items:
                item_data = {
                    "item_code": item.get("item_code"),
                    "qty": item.get("qty"),
                    "rate": item.get("rate"),
                    "warehouse": item.get("warehouse")
                }
                item_list.append(item_data)

            payment_list = []
            for payment in payments:
                payment_data = {
                    "amount": payment.get("amount"),
                    "mode_of_payment": payment.get("mode_of_payment"),
                    "base_amount": payment.get("base_amount"),
                    "account": payment.get("account")
                }
                payment_list.append(payment_data)

            # Check stock availability
            insufficient_stock_items = check_stock_availability(item_list, headers)
            if insufficient_stock_items:
                for item in insufficient_stock_items:
                    additional_qty_needed = item['required_qty'] - item['available_qty']
                    message = f"Insufficient stock for item {item['item_code']} in warehouse {item['warehouse']}. Available: {item['available_qty']}, Needed: {item['required_qty']}, Additional quantity required: {additional_qty_needed}"
                    frappe.msgprint(message)
                continue  # Skip posting this document

            posting_date_str = doc.get("posting_date").strftime("%Y-%m-%d")
            posting_time = doc.get("posting_time")
            if isinstance(posting_time, timedelta):
                posting_time_str = (datetime.min + posting_time).time().strftime("%H:%M:%S")
            else:
                posting_time_str = posting_time.strftime("%H:%M:%S")

            data = {
                "data": {
                    "customer": doc.get("customer"),
                    "pos_profile": doc.get("pos_profile"),
                    "posting_date":  posting_date_str,
                    "posting_time": posting_time_str,
                    "paid_amount": doc.get("paid_amount"),
                    "update_stock": doc.get("update_stock"),
                    "company": doc.get("company"),
                    "is_pos": 1,
                    "docstatus": doc.get("docstatus"),
                    "items": item_list,
                    "payments": payment_list
                }
            }

            # Check for duplicates before posting
            if ensure_no_duplicates_exist(doc, headers):
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                res = response.json()
                res_json = json.dumps(res)
                name = res["data"]["name"]
                frappe.db.set_value("Sales Invoice", doc["name"], "custom_return_code", "Data Posted")
                frappe.db.set_value("Sales Invoice", doc["name"], "custom_voucher_no", res["data"]["name"])
                frappe.db.commit()
                frappe.log_error(f"SI {doc['name']} posted successfully in the other PURCHASE RECEIPT.")

                # Uncheck the custom_post field
                patch_url = f"https://erp.metrogroupng.com/api/resource/Sales Invoice/{name}"
                patch_data = {"custom_voucher_no": doc["name"], "posting_date": posting_date_str}
                requests.put(patch_url, headers=headers, json=patch_data)

                # Optionally, you can enqueue a background job to process the document
                # enqueue("offline_posting.custom_api.purchase_receipt.process_document", queue='long')
            else:
                frappe.msgprint(f"Duplicates found for {doc['name']}. Skipping...")
        except (ValueError, requests.RequestException) as e:
            # Log the error
            frappe.log_error(f"Failed to post item {doc['name']}: {e}")

            # Extract errors from the response, if available
            try:
                errors = response.json().get("data", {}).get("errors")
                if errors:
                    error_message = ", ".join(errors)
                    frappe.msgprint(f"Failed to post item {doc['name']}: {error_message}")
            except KeyError:
                pass  # No errors found in the response
            break

def ensure_no_duplicates_exist(doc, headers):
    try:
        # Check if any Sales Invoice already has the same custom_voucher_no
        filters = {
            "custom_voucher_no": doc['name']
        }
        response = requests.get("https://erp.metrogroupng.com/api/resource/Sales%20Invoice",
                                params={"filters": json.dumps(filters)},
                                headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        if "data" in data:
            return len(data["data"]) == 0  # If no Sales Invoice has the same custom_voucher_no, return True (no duplicate)
        else:
            frappe.log_error("Key 'data' not found in the response: " + json.dumps(data))
            return False
    except requests.exceptions.HTTPError as http_err:
        frappe.log_error(f"HTTP error occurred: {http_err}")
        raise
    except Exception as err:
        frappe.log_error(f"Other error occurred: {err}")
        raise