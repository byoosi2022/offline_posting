import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from datetime import timedelta
import json
import requests

def get_updates_customer(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/Customer?filters=[['custom_update', '=', 1]]&fields=['customer_name','name','customer_type','customer_group','territory']"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            res = response.json()
           
            frappe.msgprint(str(res))
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
    else:
        frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")

