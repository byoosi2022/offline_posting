frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        frm.add_custom_button(
            __("Check Downloads Pending"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.count_data.get_updates_item_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>Customer Count:</strong> ${r.message.customers_count}<br>
                                    <strong>Item Price Count:</strong> ${r.message.items_price_count}<br>
                                    <strong>Item Count:</strong> ${r.message.items_count}<br>
                                    <strong>Stock Transfer Count:</strong> ${r.message.stock_transfer_count}<br>
                                    <strong>Receipt Count:</strong> ${r.message.reciept_count}<br>
                                    <strong>User Count:</strong> ${r.message.user_count}<br>
                                </div>`;
                            frappe.msgprint(message);
                        } else {
                            frappe.msgprint(__('No Unsynced Data available.'));
                        }
                    }
                });
            },
            __("Download Data")
        );
         
        frm.add_custom_button(
            __("Customer"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.customers.get_updates_customer',
                    callback: function(response) {
                        // console.log(response);
                        // Handle the response here
                    }
                });
               
                
            },
            __("Download Data")
        );
        frm.add_custom_button(
            __("Item"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.item_creation.get_updates_item',
                    callback: function(response) {
                        // console.log(response);
                        // Handle the response here
                    }
                });
               
                
            },
            __("Download Data")
        );

        frm.add_custom_button(
            __("User"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.user.get_updates_user',
                    callback: function(response) {
                        // console.log(response);
                        // Handle the response here
                    }
                });
               
                
            },
            __("Download Data")
        );

        frm.add_custom_button(
            __("Item Prices"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.item_price_update.get_updates_item_prices',
                    callback: function(response) {
                        // console.log(response);
                        // Handle the response here
                    }
                });
               
                
            },
            __("Download Data")
        );

        
        frm.add_custom_button(
            __("Purchase Reciept"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.reciept.get_submit_purchase_receipts',
                    callback: function(response) {
                        // console.log(response);
                        // Handle the response here
                    }
                });
               
                
            },
            __("Download Data")
        );
        
        frm.add_custom_button(
            __("Stock Transfer"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.sales_invoice.get_submit_stock_transfer',
                    callback: function(response) {
                         console.log(response);
                        // Handle the response here
                    }
                });
               
                
            },
            __("Download Data")
        );


        frm.add_custom_button(
            __("Check Unsynced Data"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.offline_sync.insert_invpoice_post',
                    args: { doc: frm.doc, document_type: frm.doc.document_type },
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
                    method: 'offline_posting.custom_api.purchase_reciept.post_saved_documents',
                    callback: function(response) {
                        console.log(response);
                        // Handle the response here
                    }
                });
                
            },
            __("Sync Data")
        );

        frm.add_custom_button(
            __("Sync Item"),
            function () {
                frappe.call({
                    method: 'offline_posting.api.post_item',
                    callback: function(response) {
                        // console.log(response);
                        // Handle the response here
                    }
                });
                
            },
            __("Sync Data")
        );
       
        
    }
});

frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
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


