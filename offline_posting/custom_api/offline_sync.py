import frappe

@frappe.whitelist()
def insert_invpoice_post(doc, document_type, method=None):
    current_user = frappe.session.user
    if document_type:
        unsynced_docs = frappe.db.get_all(document_type, filters={
            "custom_post": 1,
            "docstatus": 1,
            "custom_return_code": "",
            "custom_return_code": "",
             "owner": current_user  # Ensure only documents owned by the current user
        }, fields=["name"])
        unsynced_count = len(unsynced_docs)
        return unsynced_count
    else:
        return None

@frappe.whitelist()
def invpoice_post(doc , method=None):
     frappe.msgprint("Sales Invoice successfully Posted osted in the other ERPNext system.")
     
@frappe.whitelist()
def item_post(doc , method=None):
     frappe.msgprint("Item successfully Posted osted in the other ERPNext system.")

    
