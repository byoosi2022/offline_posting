frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        // Add custom button to check stock balance
        // frm.add_custom_button(__('Post To Live Site'), function() {
        //     frappe.call({
        //         method: 'offline_posting.custom_post.customer_post.post_customer',
        //         callback: function(response) {
               
        //         }
        //     });
        // });

                                   
        frm.add_custom_button(
            __("Post Directly to Live server"),
               function () {
                   frappe.call({
                       method: 'offline_posting.online_posting.customer.create_or_update_customer',
                               args:{
                                   docname: frm.doc.name
                               },
                               callback: function(response) {
                                   frappe.msgprint(response.message);
                               }
                           });
                       },
                       __("Post")
           );


        frm.add_custom_button(
            __("Check Customers on Live"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_post.checks.count_customer.get_updates_customer_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>Customer Count:</strong> ${r.message.customers_count}<br>
                                    
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
            __("Syn Customers Down"),
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
    }
});

frappe.ui.form.on('User', {
    refresh: function(frm) {
        // Add custom button to check stock balance
        frm.add_custom_button(__('Post To Live Site'), function() {
            frappe.call({
                method: 'offline_posting.custom_post.user_post.user_post',
                callback: function(response) {
               
                }
            });
        });

        frm.add_custom_button(
            __("Check Users on Live"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_post.checks.user_count.get_updates_user_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>User Count:</strong> ${r.message.users_count}<br>
                                    
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
            __("Syn User Down"),
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
    }
});

frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // Add custom button to check stock balance
        frm.add_custom_button(__('Post To Live Site'), function() {
            frappe.call({
                method: 'offline_posting.custom_post.item_post.post_item',
                callback: function(response) {
               
                }
            });
        });

        frm.add_custom_button(
            __("Check Items on Live"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_post.checks.item_count.get_updates_item_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>Item Count:</strong> ${r.message.items_count}<br>
                                    
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
            __("Syn Items Down"),
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
            __("Check Item Price on Live"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_post.checks.item_price.get_updates_item_price_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>Item Price Count:</strong> ${r.message.item_prices_count}<br>
                                    
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
            __("Syn Item Prices Down"),
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
    }
});

frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        // Add custom button to check stock balance
        frm.add_custom_button(
            __("Check Purchase Receipts on Live"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_post.checks.purchase_reciept_count.get_updates_reciept_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>Purchase Reciept Count:</strong> ${r.message.receipts_count}<br>
                                    
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
            __("Syn Purchase Receipts Down"),
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
    }
});

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        frm.add_custom_button(
            __("Check Stock Tranfers on Live"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_post.checks.stock_transfer_count.get_updates_item_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>Stock Tranfer Count:</strong> ${r.message.stock_transfers_count}<br>
                                    
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
            __("Syn Stock Tranfers Down"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.sales_invoice.get_submit_stock_transfer',
                    callback: function(response) {
                        // console.log(response);
                        // Handle the response here
                    }
                });
               
                
            },
            __("Download Data")
        );
    }
});


