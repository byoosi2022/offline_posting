import requests
import frappe

def check_internet():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        frappe.log_error("Internet available, posting saved documents")
    except requests.ConnectionError:
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()
        frappe.log_error("No internet connection")
        
        
# //"encryption_key": "peQxwpZ4oiRsTfdv2U7qSrxXCWGhHEJGKNbijF2LoNo=",
