import requests
import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json

@frappe.whitelist()
def get_updates_customer(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    for server, value in response_server.items():
        if value == 1:
            filters_customer = f'[["Customer","{server}","=","1"]]'
            url = f"https://erp.metrogroupng.com/api/resource/Customer?fields=[%22name%22,%22customer_name%22,%22customer_type%22,%22customer_group%22,%22territory%22,%22custom_update%22]&filters={filters_customer}"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"token {api_key}:{secret_key}"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                try:
                    res = response.json()
                    for customer_data in res.get('data', []):
                        update_or_create_customer(customer_data, server)
                except json.decoder.JSONDecodeError as e:
                    frappe.msgprint(f"Failed to decode JSON: {e}")
            else:
                frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")

def update_or_create_customer(customer_data, server):
    customer_name = customer_data.get('name')
    if not frappe.db.exists('Customer', customer_name):
        create_customer(customer_data)
    else:
        update_customer(customer_name, customer_data, server)

def create_customer(customer_data):
    customer = frappe.new_doc('Customer')
    set_customer_data(customer, customer_data)
    customer.insert()
    frappe.msgprint(f"Customer '{customer.customer_name}' created successfully.")

def update_customer(customer_name, customer_data, server):
    customer = frappe.get_doc('Customer', customer_name)
    if customer:
        set_customer_data(customer, customer_data)
        customer.save()
        frappe.msgprint(f"Customer '{customer.customer_name}' updated successfully.")
        uncheck_custom_update(customer_name, server)
    else:
        frappe.msgprint(f"Customer '{customer.customer_name}' not found in ERPNext.")

def set_customer_data(customer, customer_data):
    customer.customer_name = customer_data.get('customer_name', '')
    customer.customer_type = customer_data.get('customer_type', '')
    customer.customer_group = customer_data.get('customer_group', '')
    customer.territory = customer_data.get('territory', '')
    customer.custom_company = customer_data.get('custom_company', '')

def uncheck_custom_update(customer_name, server):
    api_key, secret_key = get_api_keys()
    patch_url = f"https://erp.metrogroupng.com/api/resource/Customer/{customer_name}"
    patch_data = {
        "custom_update": 0,
        f"{server}": 0
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }
    patch_response = requests.put(patch_url, headers=headers, json=patch_data)
    if patch_response.status_code == 200:
        frappe.msgprint(f"Custom update field unchecked for '{customer_name}'.")
    else:
        frappe.msgprint(f"Failed to uncheck custom update field for '{customer_name}'. Status Code: {patch_response.status_code}")

def check_internet_customer():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # frappe.log_error(f"Internet Available from Remote From Customer")
        get_updates_customer()
        
    except requests.RequestException:
        # frappe.log_error(f"No Internet Available ")
        frappe.db.set_value("System Settings", None, "custom_internet_available Customer", 0)
        frappe.db.commit()

enqueue("offline_posting.custom_api.customers.check_internet_customer", queue='long')
check_internet_customer()
