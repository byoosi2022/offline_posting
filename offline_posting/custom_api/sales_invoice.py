import requests
import frappe
from collections import defaultdict
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from frappe.utils import now_datetime

@frappe.whitelist()
def get_submit_stock_transfer(doc=None):
    try:
        api_key, secret_key = get_api_keys()
        url = "https://erp.metrogroupng.com/api/resource/Stock%20Entry?filters={%22docstatus%22:1,%22custom_post%22:1,%22stock_entry_type%22:%22Material%20Transfer%22}&fields=[%22name%22,%22from_warehouse%22,%22to_warehouse%22,%22company%22,%22posting_date%22,%22stock_entry_type%22,%22items.item_code%22,%22items.qty%22,%22items.basic_rate%22]"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {api_key}:{secret_key}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get('data', [])

        # Initialize a dictionary to store items by name
        items_by_name = defaultdict(list)

        for transfer_data in data:
            name = transfer_data.get('name')
            if name:
                items_by_name[name].append({
                    'item_code': transfer_data.get('item_code'),
                    'qty': transfer_data.get('qty', 0),
                    'basic_rate': transfer_data.get('basic_rate', 0),
                    'from_warehouse': transfer_data.get('from_warehouse'),
                    'to_warehouse': transfer_data.get('to_warehouse'),
                    'company': transfer_data.get('company'),
                    'posting_date': transfer_data.get('posting_date')
                })

        for name, items in items_by_name.items():
            transfer = frappe.new_doc('Stock Entry')
            transfer.purpose = "Material Transfer"
            transfer.stock_entry_type = "Material Transfer"
            transfer.custom_voucher_no = name
            transfer.from_warehouse = items[0]['from_warehouse']
            transfer.company = items[0]['company']
            transfer.to_warehouse = items[0]['to_warehouse']
            transfer.posting_date = items[0]['posting_date']

            for item in items:
                transfer.append('items', {
                    'item_code': item['item_code'],
                    'qty': item['qty'],
                    'basic_rate': item['basic_rate']
                })

            transfer.insert()
            transfer.submit()
            frappe.msgprint(f"Stock Transfer '{name}' created and submitted successfully.")

            # Uncheck the custom_post field
            patch_url = f"https://erp.metrogroupng.com/api/resource/Stock Entry/{name}"
            patch_data = {"custom_post": 0,"custom_voucher_no": transfer.name}
            requests.put(patch_url, headers=headers, json=patch_data)
            # frappe.log_error(f"STOCK TRANSFER '{name}' posted successfully.")

    except Exception as e:
        frappe.msgprint(f"Failed to fetch or process data: {e}")

# Define a function to check internet connection for Purchase Receipts
def check_internet_purchase_receipt():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # frappe.log_error(f"STOCK TRANSFER Internet Available.")
        # Internet connection is available, so we can attempt to post saved documents
        get_submit_stock_transfer()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.sales_invoice.check_internet_purchase_receipt", queue='long')

# Start the check_internet loop
check_internet_purchase_receipt()
