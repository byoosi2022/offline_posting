app_name = "offline_posting"
app_title = "Offline Posting"
app_publisher = "paul mututa"
app_description = "offline posting data"
app_email = "mututapaul02@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/offline_posting/css/offline_posting.css"
# app_include_js = "/assets/offline_posting/js/offline_posting.js" 
# Include JavaScript files in your app
app_include_js = [
    "/assets/offline_posting/js/custom_button.js",
    "/assets/offline_posting/js/sales_invoice.js",
    "/assets/offline_posting/js/supplier.js",
    "/assets/offline_posting/js/customer.js",
    
]


# include js, css files in header of web template
# web_include_css = "/assets/offline_posting/css/offline_posting.css"
# web_include_js = "/assets/offline_posting/js/offline_posting.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "offline_posting/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"} sites/assets/offline_posting/js/custom_button.js

doctype_js = {
    "Offline Sync": "public/js/custom_button.js",
    "Supplier": "public/js/supplier.js",
    "Customer": "public/js/customer.js",
    "Sales Invoice": "public/js/sales_invoice.js"
}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "offline_posting.utils.jinja_methods",
# 	"filters": "offline_posting.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "offline_posting.install.before_install"
# after_install = "offline_posting.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "offline_posting.uninstall.before_uninstall"
# after_uninstall = "offline_posting.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "offline_posting.utils.before_app_install"
# after_app_install = "offline_posting.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "offline_posting.utils.before_app_uninstall"
# after_app_uninstall = "offline_posting.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "offline_posting.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# "*": {
		# "on_update": "method",
	# 	"on_cancel": "method",
	# 	"on_trash": "method"
	# }
 
#    "Lead": {
#         "before_save": "offline_posting.custom_post.access_server.access_server"
#     },
   
   "Sales Invoice": {
       "validate": "offline_posting.custom_post.validate_draft.validate_sales_invoice",
       "on_submit": "offline_posting.custom_api.purchase_reciept.check_internet"
}
   
#      "Item": {
#         "on_update": "offline_posting.custom_api.offline_sync.insert_item_post"
#     },
   
#    "Offline Sync": {
#         "on_update": "offline_posting.custom_api.sales_invoice.post_saved_documents",
#         # "on_update": "offline_posting.api.post_item"
#     },
   

#     "Customer": {
#         "on_update": "offline_posting.custom_api.customers.get_updates_customer"
#     },
    
  
}

# Scheduled Tasks
# ---------------

scheduler_events = {  
    "cron": {
        "*/1 * * * *": [
            "offline_posting.custom_api.testing_internet.check_internet",
        ]
    }
    
	# "all": [
	# 	"offline_posting.tasks.all"
	# ],
	# "daily": [
	# 	"offline_posting.tasks.daily"
	# ],
	# "hourly": [
	# 	"offline_posting.tasks.hourly"
	# ],
	# "weekly": [
	# 	"offline_posting.tasks.weekly"
	# ],
	# "monthly": [
	# 	"offline_posting.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "offline_posting.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "offline_posting.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "offline_posting.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["offline_posting.utils.before_request"]
# after_request = ["offline_posting.utils.after_request"]

# Job Events
# ----------
# before_job = ["offline_posting.utils.before_job"]
# after_job = ["offline_posting.utils.after_job"]
fixtures = ['Custom Field','Offline Sync']


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"offline_posting.auth.validate"
# ]
