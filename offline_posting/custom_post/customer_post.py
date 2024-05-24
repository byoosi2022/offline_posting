import frappe # type: ignore
from frappe.utils.background_jobs import enqueue # type: ignore
from offline_posting.utils import get_api_keys
from offline_posting.custom_post.server_post import local_server
import requests
import logging

logger = logging.getLogger(__name__)

@frappe.whitelist()
def post_customer(doc=None, method=None, schedule_at=None):
    # Get API keys
    api_key, secret_key = get_api_keys()
    # Get response from local server
    response_server = local_server()
    # Get list of local customers to be posted
    local_customers = frappe.db.get_list(
        "Customer",
        filters={"custom_post": 1},
        fields=["name", "customer_name", "customer_type", "customer_group", "territory", "custom_company"]
    )

    url = "https://erp.metrogroupng.com/api/resource/Customer"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {api_key}:{secret_key}"
    }

    for local_customer in local_customers:
        customer_name = local_customer.get("name")
        check_url = f"https://erp.metrogroupng.com/api/method/metro_custom_app.api.get_all_customers_filters?name={customer_name}"
        try:
            check_response = requests.get(check_url, headers=headers)
            check_response.raise_for_status()
            remote_customers = check_response.json().get("message").get("data", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check customer '{customer_name}' existence: {e}")
            continue

        if not remote_customers:
            # Customer does not exist remotely, create it
            data = {
                "customer_name": local_customer['customer_name'],
                "customer_type": local_customer['customer_type'],
                "territory": local_customer['territory'],
                "customer_group": local_customer['customer_group'],
                "custom_company": local_customer['custom_company']
            }
            # Check if response_server is available and update the corresponding field
            for server, value in response_server.items():
                if value == 1:
                    data[server] = 0
                else:
                    data[server] = 1

            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                frappe.db.set_value("Customer", customer_name, "custom_post", 0)
                frappe.db.commit()
                frappe.msgprint(f"Customer '{local_customer['name']}' created successfully.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to create customer '{customer_name}': {e}")
            continue

        # Customer exists remotely, check for changes
        remote_customer = remote_customers[0]
        if any(local_customer[field] != remote_customer.get(field) for field in ["customer_type", "territory", "customer_group", "custom_company"]):
            # Customer has changes, update it
            patch_url = f"https://erp.metrogroupng.com/api/resource/Customer/{customer_name}"
            patch_data = {
                "customer_name": local_customer['customer_name'],
                "customer_type": local_customer['customer_type'],
                "territory": local_customer['territory'],
                "customer_group": local_customer['customer_group'],
                "custom_company": local_customer['custom_company']
            }
            # Check if response_server is available and update the corresponding field
            for server, value in response_server.items():
                if value == 1:
                    patch_data[server] = 0
                else:
                    patch_data[server] = 1

            try:
                response = requests.put(patch_url, json=patch_data, headers=headers)
                response.raise_for_status()
                frappe.db.set_value("Customer", customer_name, "custom_post", 0)
                frappe.db.commit()
                frappe.msgprint(f"Customer '{customer_name}' updated successfully.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to update customer '{customer_name}': {e}")
        else:
            logger.info(f"No changes for customer '{customer_name}'. Skipping...")


# Define a function to check internet connection for customer
def check_internet_customer():
    try:
        requests.get("http://www.google.com", timeout=5)
        frappe.db.set_value("System Settings", None, "custom_internet_available", 1)
        frappe.db.commit()
        frappe.log_error(f"Internet Availabe")
        # Internet connection is available, so we can attempt to post saved documents
        post_customer()
    except requests.RequestException:
        # No internet connection, update the database
        frappe.log_error(f"Not Internet Availabe")
        frappe.db.set_value("System Settings", None, "custom_internet_available", 0)
        frappe.db.commit()

# Schedule the job to run
enqueue("offline_posting.custom_post.customer_post.check_internet_customer", queue='short')
# Start the check_internet loop
check_internet_customer()
