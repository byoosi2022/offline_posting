import requests
import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json

@frappe.whitelist()
def get_updates_supplier(doc=None, method=None, schedule_at=None):
    response_server = local_server()
    api_key, secret_key = get_api_keys()
    for server, value in response_server.items():
        if value == 1:
            filters_supplier = f'[["Supplier","{server}","=","1"]]'
            url = f"https://erp.metrogroupng.com/api/resource/Supplier?fields=[%22name%22,%22supplier_name%22,%22supplier_type%22,%22supplier_group%22,%22country%22,%22custom_company%22]&filters={filters_supplier}"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"token {api_key}:{secret_key}"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                try:
                    res = response.json()
                    for supplier_data in res.get('data', []):
                        update_or_create_supplier(supplier_data, server)
                except json.decoder.JSONDecodeError as e:
                    frappe.msgprint(f"Failed to decode JSON: {e}")
            else:
                frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")

def update_or_create_supplier(supplier_data, server):
    supplier_name = supplier_data.get('name')
    if not frappe.db.exists('Supplier', supplier_name):
        create_supplier(supplier_data)
    else:
        update_supplier(supplier_name, supplier_data, server)

def create_supplier(supplier_data):
    supplier = frappe.new_doc('Supplier')
    set_supplier_data(supplier, supplier_data)
    supplier.insert()
    frappe.msgprint(f"Supplier '{supplier.supplier_name}' created successfully.")

def update_supplier(supplier_name, supplier_data, server):
    supplier = frappe.get_doc('Supplier', supplier_name)
    if supplier:
        set_supplier_data(supplier, supplier_data)
        supplier.save()
        frappe.msgprint(f"Supplier '{supplier.supplier_name}' updated successfully.")
        uncheck_custom_update(supplier_name, server)
    else:
        frappe.msgprint(f"Supplier '{supplier.supplier_name}' not found in ERPNext.")

def set_supplier_data(supplier, supplier_data):
    supplier.supplier_name = supplier_data.get('supplier_name', '')
    supplier.supplier_type = supplier_data.get('supplier_type', '')
    supplier.supplier_group = supplier_data.get('supplier_group', '')
    supplier.country = supplier_data.get('country', '')
    supplier.custom_company = supplier_data.get('custom_company', '')

def uncheck_custom_update(supplier_name, server):
    api_key, secret_key = get_api_keys()
    patch_url = f"https://erp.metrogroupng.com/api/resource/Supplier/{supplier_name}"
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
        frappe.msgprint(f"Custom update field unchecked for '{supplier_name}'.")
    else:
        frappe.msgprint(f"Failed to uncheck custom update field for '{supplier_name}'. Status Code: {patch_response.status_code}")

def check_internet_supplier():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # frappe.log_error(f"Internet Available from Remote Fom supplier_live")
        get_updates_supplier()
        
    except requests.RequestException:
        
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()
        # frappe.log_error(f"No Internet Available From supplier_live")

enqueue("offline_posting.custom_api.supplier_live.check_internet_supplier", queue='short')
check_internet_supplier()
