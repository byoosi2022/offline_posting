import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import json
import requests

@frappe.whitelist()
def user_post(doc=None, method=None, schedule_at=None):
    api_key, secret_key = get_api_keys()
    live_users = set(fetch_live_user_names(api_key, secret_key))
    local_users = frappe.db.get_list("User", filters={"custom_post": 1}, fields=["name", "email","last_name","full_name", "role_profile_name", "first_name"])

    url = "https://erp.metrogroupng.com/api/resource/User"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    for local_user in local_users:
        if local_user['name'] in live_users:
            # Updated if it exists
            patch_url = f"https://erp.metrogroupng.com/api/resource/User/{local_user['name']}"
            patch_data = {
                "full_name": local_user['full_name'],
                "role_profile_name": local_user['role_profile_name'],
                "first_name": local_user['first_name'],
                "last_name": local_user['last_name']
            }
            # Check if response_server is available and update the corresponding field
            response_server = local_server()
            if response_server:
                for server, value in response_server.items():
                    if value == 1:
                        patch_data[server] = 0
                    else:
                        patch_data[server] = 1
            
            patch_response = requests.put(patch_url, headers=headers, json=patch_data)
            if patch_response.status_code == 200:
                frappe.db.set_value("User", local_user['name'], "custom_post", 0)
                frappe.db.commit()
                frappe.log_error(f"User {local_user['name']} posted successfully in the other System.")
                frappe.msgprint(f"Custom update field unchecked for '{local_user['name']}'.")
            else:
                frappe.msgprint(f"Failed to uncheck custom update field for '{local_user['name']}'. Status Code: {patch_response.status_code}")
       
            frappe.msgprint(f"User <a href='https://erp.metrogroupng.com/app/user/{local_user['name']}'>{local_user['name']}</a> already exists in live site ")
            continue

        data = {
                "email": local_user['email'],
                "full_name": local_user['full_name'],
                "role_profile_name": local_user['role_profile_name'],
                "first_name": local_user['first_name'],
                "last_name": local_user['last_name']
        }
        # Check if response_server is available and update the corresponding field
        response_server = local_server()
        if response_server:
            for server, value in response_server.items():
                if value == 1:
                    data[server] = 0
                else:
                    data[server] = 1

        response = requests.post(url, json=data, headers=headers)

        try:
            res = response.json()
            if res.get('status') == 'ok':
                frappe.db.set_value("User", local_user['name'], "custom_post", 0)
                frappe.db.commit()
                frappe.log_error(f"User {local_user['name']} posted successfully in the other System.")
                frappe.msgprint("Data posted successfully")
            else:
                print("Failed to post data")
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")


def fetch_live_user_names(api_key, secret_key):
    url = "https://erp.metrogroupng.com/api/method/metro_custom_app.api.get_all_users"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        try:
            res = response.json()
            if 'message' in res and 'data' in res['message']:
                users = res['message']['data']
                if isinstance(users, list):
                    return [user["name"] for user in users]
                else:
                    frappe.msgprint(f"Invalid data format received: {type(users)}")
                    return []
            else:
                frappe.msgprint("Invalid data format received: 'message' or 'data' key not found in response")
                return []
        except json.decoder.JSONDecodeError as e:
            frappe.msgprint(f"Failed to decode JSON: {e}")
            return []
    else:
        frappe.msgprint(f"Failed to fetch data: {response.status_code} - {response.text}")
        return []
    
# Define a function to check internet connection for user
def check_internet_user():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        # Internet connection is available, so we can attempt to post saved documents
        user_post()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule check_internet function to run every 10 seconds
enqueue("offline_posting.custom_post.user_post.check_internet_user", queue='long')

# Start the check_internet loop
check_internet_user()
