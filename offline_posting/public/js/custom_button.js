frappe.ui.form.on('Offline Sync', {
    refresh: function(frm) {
        frm.add_custom_button(
            __("Check Downloads Pending"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.count_data.get_updates_item_count',
                    callback: function(r) {
                        // console.log(r);
                        if (r.message !== null) {
                            var message = __("Customer Count: {0}, Item Price Count: {1}, Item Count: {2}, stock transfer Count: {3},Reciept Count: {4}");
                            var counts = [
                                r.message.customers_count,
                                r.message.items_price_count,
                                r.message.items_count,
                                r.message.stock_transfer_count,
                                r.message.reciept_count
                            ];
                            frappe.msgprint(__(message, counts));
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
                    method: 'offline_posting.custom_api.sales_invoice.post_saved_documents',
                    callback: function(response) {
                        // console.log(response);
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
