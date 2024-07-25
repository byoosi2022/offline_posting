import requests
import frappe
from offline_posting.utils import get_api_keys

@frappe.whitelist()
def post_saved_documents(doc=None, method=None, warehouse=None, item_code=None):
    api_key, secret_key = get_api_keys()
    url = f"https://erp.metrogroupng.com/api/resource/Bin"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }
    params = {
        "fields": '["actual_qty", "item_code", "warehouse"]',
        "filters": f'[["Bin", "warehouse", "=", "{warehouse}"], ["Bin", "item_code", "=", "{item_code}"]]'
    }

    try:
        # Get filtered Bins from https://erp.metrogroupng.com/
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            erp_bins = response.json()
            return erp_bins
        else:
            frappe.msgprint(f"Error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        frappe.msgprint(f"RequestException: {e}")


