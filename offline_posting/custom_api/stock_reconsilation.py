import requests
import frappe
from collections import defaultdict
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server

@frappe.whitelist()
def get_submit_stock_reconciliations():
    try:
        api_key, secret_key = get_api_keys()
        response_server = local_server()
        # Check if response_server is available and update the corresponding field
        for server, value in response_server.items():
            if value == 1:
                filters_reconciliation = f'[["Stock Reconciliation","docstatus","=","1"],["Stock Reconciliation","{server}","=","1"]]'
                url = f"https://erp.metrogroupng.com/api/resource/Stock%20Reconciliation?filters={filters_reconciliation}&fields=[%22name%22,%22posting_date%22,%22posting_time%22,%22company%22,%22items.item_code%22,%22items.qty%22,%22items.valuation_rate%22,%22purpose%22,%22set_warehouse%22,%22expense_account%22]&limit_page_length=1000"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"token {api_key}:{secret_key}"
                }

                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json().get('data', [])

                # Initialize a dictionary to store items by name
                items_by_name = defaultdict(list)

                for reconciliation_data in data:
                    name = reconciliation_data.get('name')
                    if name:
                        items_by_name[name].append({
                            'item_code': reconciliation_data.get('item_code'),
                            'qty': reconciliation_data.get('qty', 0),
                            'valuation_rate': reconciliation_data.get('valuation_rate', 0),
                            'company': reconciliation_data.get('company'),
                            'posting_date': reconciliation_data.get('posting_date'),
                            'posting_time': reconciliation_data.get('posting_time'),
                            'purpose': reconciliation_data.get('purpose'),
                            'set_warehouse': reconciliation_data.get('set_warehouse'),
                            'expense_account': reconciliation_data.get('expense_account')
                        })

                for name, items in items_by_name.items():
                    # Check if a Stock Reconciliation with this custom_voucher_no already exists
                    if not frappe.db.exists('Stock Reconciliation', {'custom_voucher_no': name}):
                        reconciliation = frappe.new_doc('Stock Reconciliation')
                        company = items[0]['company']
                        posting_date = items[0]['posting_date']
                        posting_time = items[0]['posting_time']
                        purpose = items[0]['purpose']
                        default_warehouse = items[0]['default_warehouse']
                        difference_account_cost_center = items[0]['difference_account_cost_center']

                        reconciliation.company = company
                        reconciliation.posting_date = posting_date
                        reconciliation.posting_time = posting_time
                        reconciliation.purpose = purpose
                        reconciliation.default_warehouse = default_warehouse
                        reconciliation.difference_account_cost_center = difference_account_cost_center
                        reconciliation.custom_voucher_no = name

                        for item in items:
                            item_code = item['item_code']
                            qty = item['qty']
                            valuation_rate = item['valuation_rate']

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

                            reconciliation.append('items', {
                                'item_code': item_code,
                                'qty': qty,
                                'valuation_rate': valuation_rate
                            })

                        reconciliation.insert()
                        reconciliation.submit()
                        frappe.msgprint(f"Stock Reconciliation '{name}' created and submitted successfully.")

                        # Uncheck the custom_post field
                        patch_url = f"https://erp.metrogroupng.com/api/resource/Stock%20Reconciliation/{name}"
                        patch_data = {
                            "custom_post": 0,
                            f"{server}": 0
                        }

                        requests.put(patch_url, headers=headers, json=patch_data)

    except Exception as e:
        frappe.msgprint(f"Failed to fetch or process data: {e}")

# Define a function to check internet connection for Stock Reconciliations
def check_internet_stock_reconciliation():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        get_submit_stock_reconciliations()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.stock_reconsilation.check_internet_stock_reconciliation", queue='short')

# Start the check_internet loop
check_internet_stock_reconciliation()
