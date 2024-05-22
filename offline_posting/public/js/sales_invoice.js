frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        // Add custom button to check stock balance
        frm.add_custom_button(__('Check Stock Balance'), function() {
            frm.doc.items.forEach(function(item, index) {
                // Call custom API to check stock balance
                frappe.call({
                    method: 'offline_posting.custom_api.check_stock_balance.post_saved_documents',
                    args: {
                        item_code: item.item_code,
                        warehouse: item.warehouse
                    },
                    callback: function(response) {
                        console.log('Response:', response);
                        if (response.message && response.message.data && response.message.data.length > 0) {
                            var actual_qty = response.message.data[0].actual_qty;
                            frappe.model.set_value('Sales Invoice Item', item.name, 'custom_online_stock_balance', actual_qty);
                            frm.refresh_field('items');
                        } else {
                            console.log('No balance data received.');
                        }
                    }
                });
            });
        });
        frm.add_custom_button(
            __("Check Unsynced Data"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.offline_sync.insert_invpoice_post',
                    args: { doc: frm.doc,
                            document_type: "Sales Invoice"},
                    callback: function(r) {
                        // console.log(r);
                        if (r.message !== null) {
                            frappe.msgprint(__('Unsynced Data Count: {0}', [r.message]));
                            // console.log(r.message);
                        } else {
                            frappe.msgprint(__('No Unsynced Data for {0} Count:', [frm.doc.document_type]));
                        }
                    }
                });
               
                
            },
            __("Sync Data")
        );
        frm.add_custom_button(
            __("Sync Invoice"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.sales.post_saved_documents',
                    callback: function(response) {
                        console.log(response);
                        // Handle the response here
                    }
                });
                
            },
            __("Sync Data")
        );


    }
});
