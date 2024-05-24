import requests
import frappe
from collections import defaultdict
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server

@frappe.whitelist()
def get_submit_stock_transfer(doc=None):
    try:
        api_key, secret_key = get_api_keys()
        response_server = local_server()
        # Check if response_server is available and update the corresponding field
        for server, value in response_server.items():
            if value == 1:
                filters_stock_transfer = f'[["Stock Entry","{server}","=","1"],["Stock Entry","stock_entry_type","=","Material Transfer"],["Stock Entry","docstatus","=","1"],["Stock Entry","custom_voucher_no","=",""]]'
                url = f"https://erp.metrogroupng.com/api/resource/Stock%20Entry?filters={filters_stock_transfer}&fields=[%22name%22,%22from_warehouse%22,%22to_warehouse%22,%22company%22,%22posting_date%22,%22stock_entry_type%22,%22items.item_code%22,%22items.qty%22,%22items.basic_rate%22,%22items.cost_center%22,%22items.t_warehouse%22,%22items.s_warehouse%22]"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"token {api_key}:{secret_key}"
                }

                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json().get('data', [])

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
                            'posting_date': transfer_data.get('posting_date'),
                            's_warehouse': transfer_data.get('s_warehouse', ''),
                            't_warehouse': transfer_data.get('t_warehouse', ''),
                            'cost_center': transfer_data.get('cost_center'),
                        })

                for name, items in items_by_name.items():
                    # Check if a Stock Entry with this custom_voucher_no already exists
                    if not frappe.db.exists('Stock Entry', {'custom_voucher_no': name}):
                        transfer = frappe.new_doc('Stock Entry')
                        transfer.purpose = "Material Transfer"
                        transfer.stock_entry_type = "Material Transfer"
                        transfer.custom_voucher_no = name
                        transfer.company = items[0]['company']
                        transfer.posting_date = items[0]['posting_date']

                        for item in items:
                            item_code = item['item_code']
                            if not frappe.db.exists('Item', item_code):
                                new_item = frappe.new_doc('Item')
                                new_item.item_code = item_code
                                new_item.item_group = 'All Item Groups'
                                new_item.custom_company = item['company']
                                new_item.valuation_rate = 2000
                                new_item.insert()

                            transfer.append('items', {
                                'item_code': item_code,
                                'qty': item['qty'],
                                'basic_rate': item['basic_rate'],
                                's_warehouse': item['s_warehouse'],
                                't_warehouse': item['t_warehouse'],
                                'cost_center': item['cost_center'],
                            })

                        for item_with_valuation_rate in items:
                            valuation_rate = frappe.db.get_value('Item', item_with_valuation_rate['item_code'], 'valuation_rate')
                            frappe.msgprint(str(valuation_rate))
                            if valuation_rate == 0.0:
                                valuation_rate = 2000
                                frappe.db.set_value("Item", item_with_valuation_rate['item_code'], "valuation_rate", valuation_rate)
                                frappe.db.commit()

                        transfer.insert()
                        transfer.submit()
                        frappe.msgprint(f"Stock Transfer '{name}' created and submitted successfully.")

                        patch_url = f"https://erp.metrogroupng.com/api/resource/Stock Entry/{name}"
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
        get_submit_stock_transfer()

    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.sales_invoice.check_internet_purchase_receipt", queue='short')

# Start the check_internet loop
check_internet_purchase_receipt()
