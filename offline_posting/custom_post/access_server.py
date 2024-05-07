import frappe
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import requests

@frappe.whitelist()
def access_server(doc=None, method=None, schedule_at=None):
    # Get API keys
    api_key, secret_key = get_api_keys()
    # Get servers
    response = local_server()
    frappe.msgprint(f"{response}")


        
