import requests
import frappe
from frappe.utils.background_jobs import enqueue
from offline_posting.utils import get_api_keys
from datetime import timedelta
import json

# # Schedule check_internet function to run every 10 seconds
# enqueue("offline_posting.custom_api.testing_internet.check_internet", queue='long')

# def check_internet(doc=None,method=None):
#     try:
#         requests.get("http://www.google.com", timeout=5)
#         frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
#         frappe.db.commit()
#         frappe.log_error("internet connection Available testing_internet")
   
#     except requests.RequestException:
#         frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
#         frappe.db.commit()
#         frappe.msgprint("No internet connection")
#         frappe.log_error("No internet connection")

# check_internet()  # Start the check_internet loop

import time

def check_internet(doc=None, method=None):
    while True:
        try:
            requests.get("http://www.google.com", timeout=5)
            frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
            frappe.db.commit()
            frappe.log_error("Internet connection available")
        except requests.RequestException:
            frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
            frappe.db.commit()
            frappe.msgprint("No internet connection")
            frappe.log_error("No internet connection")
        time.sleep(10)  # Wait for 10 seconds before checking again
        
enqueue("offline_posting.custom_api.sales_invoice.check_internet", queue='long')
check_internet()  # Start the check_internet loop

