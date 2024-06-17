import json
import requests
import frappe

@frappe.whitelist()
def get_api_keys():
    username = frappe.session.user
    pwd = frappe.get_doc("User", username)
    password = pwd.get("custom_password")
    
    url_login = f"https://erp.metrogroupng.com/api/method/metro_custom_app.custom_api.auth.login?usr={username}&pwd={password}"
    response_login = requests.get(url_login)
    result_login = response_login.json()
    api_key = result_login.get("message", {}).get("api_key")
    secret_key = result_login.get("message", {}).get("api_secret")
    
    if not api_key or not secret_key:
        frappe.msgprint("Failed to get API keys")
        return None, None

    return api_key, secret_key

@frappe.whitelist()
def get_api_keys12():
    username = frappe.session.user
    pwd = frappe.get_doc("User", username)
    password = pwd.get("custom_password")
    
    server = "https://erp.metrogroupng.com"
    
    url_login = f"{server}/api/method/metro_custom_app.custom_api.auth.login?usr={username}&pwd={password}"
    response_login = requests.get(url_login)
    result_login = response_login.json()
    api_key = result_login.get("message", {}).get("api_key")
    secret_key = result_login.get("message", {}).get("api_secret")
    
    if not api_key or not secret_key:
        frappe.msgprint(f"Failed to get API keys for {server}")
        return None, None
    
    return [(api_key, secret_key)]


