import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from datetime import timedelta
import json
import requests

@frappe.whitelist()
def get_updates_customer(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Customer?fields=[%22name%22,%22customer_name%22,%22customer_type%22,%22customer_group%22,%22territory%22]&filters=[[%22Customer%22,%22custom_update%22,%22=%22,%221%22]]"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            res = response.json()
            for customer_data in res.get('data', []):
                customer_name = customer_data.get('name')
                if not frappe.db.exists('Customer', customer_name):
                    customer = frappe.new_doc('Customer')
                    customer.customer_name = customer_data.get('customer_name', '')
                    customer.customer_type = customer_data.get('customer_type', '')
                    customer.customer_group = customer_data.get('customer_group', '')
                    customer.territory = customer_data.get('territory', '')
                    customer.custom_company = customer_data.get('custom_company', '')
                    customer.insert()
                    frappe.msgprint(f"Customer '{customer_name}' created successfully.")
                else:
                    customer = frappe.get_doc('Customer', customer_name)
                    if customer:
                        customer.customer_name = customer_data.get('customer_name', '')
                        customer.customer_type = customer_data.get('customer_type', '')
                        customer.customer_group = customer_data.get('customer_group', '')
                        customer.territory = customer_data.get('territory', '')
                        customer.save()
                        frappe.msgprint(f"Customer '{customer_name}' updated successfully.")
                    else:
                        frappe.msgprint(f"Customer '{customer_name}' not found in ERPNext.")
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
    else:
        frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")
