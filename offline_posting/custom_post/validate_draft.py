import frappe
from frappe import _

def validate_sales_invoice(doc, method):
    items_with_insufficient_stock = []

    # Iterate through the items in the Sales Invoice document
    for item in doc.items:
        # Check if the item is a stock item
        maintain_stock = frappe.get_value("Item", item.item_code, "is_stock_item")
        if maintain_stock:
            # Fetch the actual stock quantity in the specific warehouse
            actual_qty = frappe.db.get_value("Bin", {"item_code": item.item_code, "warehouse": item.warehouse}, "actual_qty") or 0

            # If the required quantity is more than the available stock
            if item.qty > actual_qty:
                item_doc = frappe.get_doc("Item", item.item_code)
                items_with_insufficient_stock.append({
                    "item_code": item.item_code,
                    "item_name": item_doc.item_name,
                    "warehouse": item.warehouse,
                    "qty_needed": item.qty - actual_qty
                })

    # If there are items with insufficient stock, throw an error and prevent the document from saving
    if items_with_insufficient_stock:
        error_message = "".join(
            f"Item Code: <b>{item['item_code']}</b><br>Warehouse: <b>{item['warehouse']}</b><br>Qty Needed: {item['qty_needed']}<br><br>"
            for item in items_with_insufficient_stock
        )

        frappe.local.flags.error_message_html = True
        frappe.throw(_("Insufficient Stock For: <br>{0}").format(error_message))

# Register the function to the validate event of Sales Invoice
def register_validate_sales_invoice():
    if not hasattr(frappe.db, 'validate_sales_invoice'):
        frappe.db.validate_sales_invoice = validate_sales_invoice

    frappe.get_hooks("doc_events")["Sales Invoice"] = {}
    frappe.get_hooks("doc_events")["Sales Invoice"]["validate"] = "offline_posting.custom_post.validate_draft.validate_sales_invoice"

register_validate_sales_invoice()
