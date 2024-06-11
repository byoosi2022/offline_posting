import frappe # type: ignore

@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
    try:
        frappe.logger().info(f"Attempting login for user: {usr}")

        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        user = frappe.get_doc('User', frappe.session.user)

        # Generate a new API secret key for the user
        new_api_secret = user.custom_secret

        frappe.response["message"] = {
            "sid": frappe.session.sid,
            "user": user.name,
            "api_key": user.api_key,
            "api_secret": new_api_secret
        }
        frappe.logger().info(f"Login successful for user: {usr}")
        return

    except frappe.exceptions.AuthenticationError as e:
        frappe.logger().error(f"Authentication failed for user: {usr} - {e}")
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Authentication Failed"
        }
        return

    except Exception as e:
        frappe.logger().error(f"Unexpected error during login for user: {usr} - {e}")
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": f"An unexpected error occurred: {e}"
        }
        return


