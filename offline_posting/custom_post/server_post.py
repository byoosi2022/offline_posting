import frappe # type: ignore

@frappe.whitelist()
def local_server():
    try:
        servers = frappe.db.get_all("Offline Sync", fields=["custom_local_server_1","sever_for_developer","custom_local_server_2","custom_local_server_3"])
        # Initialize a dictionary to store keys and their values
        server_values = {}
        # Iterate over each server dictionary
        for server in servers:
            # Iterate over each key-value pair in the server dictionary
            for key, value in server.items():
                # Add the key-value pair to the dictionary
                server_values[key] = value
        # Return the dictionary containing keys and their values
        return server_values
    except Exception as e:
        frappe.log_error(f"Failed to fetch customers: {e}")
        return frappe.utils.response.report_error("Failed to fetch customers")

