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
    }
});
