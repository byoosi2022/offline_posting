import frappe
import requests
from collections import defaultdict
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys

@frappe.whitelist()
def get_submit_purchase_receipts():
    try:
        api_key, secret_key = get_api_keys()
        url = "https://erp.metrogroupng.com/api/resource/Purchase%20Receipt?filters={%22docstatus%22:1,%22custom_post%22:1}&fields=[%22name%22,%22supplier%22,%22posting_date%22,%22company%22,%22items.item_code%22,%22items.qty%22,%22items.rate%22]"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {api_key}:{secret_key}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get('data', [])

        # Initialize a dictionary to store items by name
        items_by_name = defaultdict(list)

        for receipt_data in data:
            name = receipt_data.get('name')
            if name:
                items_by_name[name].append({
                    'item_code': receipt_data.get('item_code'),
                    'qty': receipt_data.get('qty', 0),
                    'rate': receipt_data.get('rate', 0),
                    'supplier': receipt_data.get('supplier'),
                    'company': receipt_data.get('company'),
                    'posting_date': receipt_data.get('posting_date')
                })

        for name, items in items_by_name.items():
            receipt = frappe.new_doc('Purchase Receipt')
            receipt.supplier = items[0]['supplier']
            receipt.company = items[0]['company']
            receipt.posting_date = items[0]['posting_date']

            for item in items:
                receipt.append('items', {
                    'item_code': item['item_code'],
                    'qty': item['qty'],
                    'rate': item['rate']
                })

            receipt.insert()
            receipt.submit()
            frappe.msgprint(f"Purchase Receipt '{name}' created and submitted successfully.")

            # Uncheck the custom_post field
            patch_url = f"https://erp.metrogroupng.com/api/resource/Purchase Receipt/{name}"
            patch_data = {"custom_post": 0,"custom_voucher_no": receipt.name}
            requests.put(patch_url, headers=headers, json=patch_data)

    except Exception as e:
        frappe.msgprint(f"Failed to fetch or process data: {e}")

# Define a function to check internet connection for Purchase Receipts
def check_internet_purchase_receipt():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        get_submit_purchase_receipts()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.sales_invoice.check_internet_purchase_receipt", queue='long')

# Start the check_internet loop
check_internet_purchase_receipt()