import requests
import frappe
from offline_posting.utils import get_api_keys

@frappe.whitelist()
def post_saved_documents(doc=None, method=None, warehouse=None, item_code=None):
    api_key, secret_key = get_api_keys()
    url = f"https://erp.metrogroupng.com/api/resource/Bin?fields=[%22actual_qty%22,%22item_code%22,%22warehouse%22]&filters=[[%22Bin%22,%22warehouse%22,%22=%22,%22{warehouse}%22],[%22Bin%22,%22item_code%22,%22=%22,%22{item_code}%22]]"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    try:
        # Get filtered Bins from https://erp.metrogroupng.com/
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            erp_bins = response.json()
            return erp_bins
        else:
            frappe.msgprint(f"Error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print("Error:", e)


