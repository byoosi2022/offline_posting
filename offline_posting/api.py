import requests
import frappe
from offline_posting.utils import get_api_keys
import json
from frappe.utils.background_jobs import enqueue

@frappe.whitelist()
def get_updates_purchase_receipt(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Purchase%20Receipt?filters=%7B%22docstatus%22%3A1%2C%22custom_post%22%3A1%7D&fields=%5B%22name%22%2C%22set_warehouse%22%2C%22items%22%5D"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            res = response.json()
            for receipt_data in res.get('data', []):
                receipt_name = receipt_data.get('name')
                set_warehouse = receipt_data.get('set_warehouse')
                items = receipt_data.get('items')
                if receipt_name:
                    if not frappe.db.exists('Purchase Receipt', receipt_name):
                        receipt = frappe.new_doc('Purchase Receipt')
                        receipt.name = receipt_name
                        receipt.set_warehouse = set_warehouse
                        for item in items:
                            receipt.append('items', {
                                'item_code': item.get('item_code'),
                                'qty': item.get('qty'),
                                'rate': item.get('rate'),
                                # Add other item fields as needed
                            })
                        receipt.insert()
                        frappe.msgprint(f"Purchase Receipt '{receipt_name}' created successfully.")
                    else:
                        receipt = frappe.get_doc('Purchase Receipt', receipt_name)
                        if receipt:
                            receipt.set_warehouse = set_warehouse
                            receipt.items = []  # Clear existing items to prevent duplication
                            for item in items:
                                receipt.append('items', {
                                    'item_code': item.get('item_code'),
                                    'qty': item.get('qty'),
                                    'rate': item.get('rate'),
                                    # Add other item fields as needed
                                })
                            receipt.save()
                            frappe.msgprint(f"Purchase Receipt '{receipt_name}' updated successfully.")
                        else:
                            frappe.msgprint(f"Purchase Receipt '{receipt_name}' not found in ERPNext.")
                else:
                    frappe.msgprint("Skipping Purchase Receipt update: Name not provided.")
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
    else:
        frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")

# Define a function to check internet connection for Purchase Receipts
def check_internet_purchase_receipt():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        get_updates_purchase_receipt()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.purchase_receipt_creation.check_internet_purchase_receipt", queue='long')

# Start the check_internet loop
check_internet_purchase_receipt()

import frappe
import json

@frappe.whitelist()
def get_all_customers():
    try:
        customers = frappe.db.get_all("Customer", fields=["name", "customer_name", "customer_type", "customer_group", "territory"])
        return customers
    except Exception as e:
        frappe.log_error(f"Failed to fetch customers: {e}")
        return frappe.utils.response.report_error("Failed to fetch customers")
    
import frappe
from frappe import _

def validate_sales_invoice(doc, method):
    items_with_insufficient_stock = []
    
    for item in doc.items:
        maintain_stock = frappe.get_value("Item", item.item_code, "is_stock_item")
        if maintain_stock:
            # Fetch the actual stock quantity in the specific warehouse
            actual_qty = frappe.db.get_value("Bin", {"item_code": item.item_code, "warehouse": item.warehouse}, "actual_qty") or 0
            
            if item.qty > actual_qty:
                item_doc = frappe.get_doc("Item", item.item_code)
                items_with_insufficient_stock.append({
                    "item_code": item.item_code,
                    "item_name": item_doc.item_name,
                    "warehouse": item.warehouse,
                    "qty_needed": item.qty - actual_qty
                })

    if items_with_insufficient_stock:
        error_message = ""
        for item in items_with_insufficient_stock:
            error_message += f"Item Code: <b>{item['item_code']}</b><br>Warehouse: <b>{item['warehouse']}</b><br>Qty Needed: {item['qty_needed']}<br><br>"

        frappe.local.flags.error_message_html = True
        frappe.throw(_("Insufficient Stock For: <br>{0}").format(error_message))

