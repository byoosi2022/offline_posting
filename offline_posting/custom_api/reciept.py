import requests
import frappe
from collections import defaultdict
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server

@frappe.whitelist()
def get_submit_purchase_receipts():
    try:
        api_key, secret_key = get_api_keys()
        response_server = local_server()
        # Check if response_server is available and update the corresponding field
        for server, value in response_server.items():
            if value == 1:
                filters_receipt = f'[["Purchase Receipt","docstatus","=","1"],["Purchase Receipt","{server}","=","1"],["Purchase Receipt","custom_voucher_no","=",""]]'
                url = f"https://erp.metrogroupng.com/api/resource/Purchase%20Receipt?filters={filters_receipt}&fields=[%22name%22,%22supplier%22,%22posting_date%22,%22company%22,%22set_warehouse%22,%22items.item_code%22,%22items.qty%22,%22items.rate%22]&limit_page_length=1000"
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
                            'posting_date': receipt_data.get('posting_date'),
                            'set_warehouse': receipt_data.get('set_warehouse')
                        })

                for name, items in items_by_name.items():
                    # Check if a Purchase Receipt with this custom_voucher_no already exists
                    if not frappe.db.exists('Purchase Receipt', {'custom_voucher_no': name}):
                        receipt = frappe.new_doc('Purchase Receipt')
                        supplier = items[0]['supplier']
                        company = items[0]['company']
                        posting_date = items[0]['posting_date']
                        set_warehouse = items[0]['set_warehouse']

                        # Check if the supplier exists
                        if not frappe.db.exists('Supplier', supplier):
                            # Create a new supplier if it doesn't exist
                            new_supplier = frappe.new_doc('Supplier')
                            new_supplier.supplier_name = supplier
                            new_supplier.supplier_type = 'Company'  # Assuming supplier type
                            new_supplier.supplier_group = 'All Supplier Groups'
                            new_supplier.custom_company = company
                            new_supplier.insert()

                        receipt.supplier = supplier
                        receipt.company = company
                        receipt.posting_date = posting_date
                        receipt.set_warehouse = set_warehouse
                        receipt.custom_voucher_no = name

                        for item in items:
                            item_code = item['item_code']
                            qty = item['qty']
                            rate = item['rate']

                            # Check if the item exists
                            if not frappe.db.exists('Item', item_code):
                                # Create a new item if it doesn't exist
                                new_item = frappe.new_doc('Item')
                                new_item.item_code = item_code
                                new_item.item_name = item_code
                                new_item.item_group = 'All Item Groups'
                                new_item.is_stock_item = 1
                                new_item.custom_company = company
                                new_item.insert()

                            receipt.append('items', {
                                'item_code': item_code,
                                'qty': qty,
                                'rate': rate
                            })

                        receipt.insert()
                        receipt.submit()
                        frappe.msgprint(f"Purchase Receipt '{name}' created and submitted successfully.")

                        # Uncheck the custom_post field
                        patch_url = f"https://erp.metrogroupng.com/api/resource/Purchase%20Receipt/{name}"
                        patch_data = {
                            "custom_post": 0,
                            f"{server}": 0
                        }

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
enqueue("offline_posting.custom_api.reciept.check_internet_purchase_receipt", queue='short')

# Start the check_internet loop
check_internet_purchase_receipt()
