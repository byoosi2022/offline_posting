import requests
import frappe
from frappe.utils.background_jobs import enqueue
import time

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

# Run the function once to check the internet status
check_internet()

# Enqueue the function call for periodic checking (e.g., every minute)
enqueue("offline_posting.api.check_internet", queue='long', interval=60)
