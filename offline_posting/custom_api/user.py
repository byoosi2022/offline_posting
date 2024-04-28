import requests
import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
import json 

@frappe.whitelist()
def get_updates_user(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    url = "https://erp.metrogroupng.com/api/resource/User?fields=[%22name%22,%22first_name%22,%22last_name%22,%22email%22,%22role_profile_name%22,%22custom_update%22]&filters=[[%22User%22,%22custom_update%22,%22=%22,%221%22]]"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            res = response.json()
            for user_data in res.get('data', []):
                user_name = user_data.get('name')
                if not frappe.db.exists('User', user_name):
                    user = frappe.new_doc('User')
                    user.first_name = user_data.get('first_name', '')
                    user.last_name = user_data.get('last_name', '')
                    user.email = user_data.get('email', '')
                    user.role_profile_name = user_data.get('role_profile_name', '')
                    user.insert()
                    frappe.msgprint(f"User '{user_name}' created successfully.")
                else:
                    user = frappe.get_doc('User', user_name)
                    if user:
                        user.first_name = user_data.get('first_name', '')
                        user.last_name = user_data.get('last_name', '')
                        user.email = user_data.get('email', '')
                        user.role_profile_name = user_data.get('role_profile_name', '')
                        user.save()
                        frappe.msgprint(f"User '{user_name}' updated successfully.")
                        # Uncheck the custom_update field
                        patch_url = f"https://erp.metrogroupng.com/api/resource/User/{user_name}"
                        patch_data = {
                            "custom_update": 0
                        }
                        patch_response = requests.put(patch_url, headers=headers, json=patch_data)
                        if patch_response.status_code == 200:
                            frappe.msgprint(f"Custom update field unchecked for '{user_name}'.")
                        else:
                            frappe.msgprint(f"Failed to uncheck custom update field for '{user_name}'. Status Code: {patch_response.status_code}")
                    else:
                        frappe.msgprint(f"User '{user_name}' not found in Frappe.")
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
    else:
        frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")

# Define a function to check internet connection for user
def check_internet_user():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to synchronize users
        get_updates_user()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_api.user.check_internet_user", queue='long')

# Start the check_internet loop
check_internet_user()
