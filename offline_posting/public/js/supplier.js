frappe.ui.form.on('Supplier', {
    refresh: function(frm) {
        // Add custom button to check stock balance
        frm.add_custom_button(__('Post To Live Site'), function() {
     
                frappe.call({
                    method: 'offline_posting.custom_post.supplier_post.post_supplier',
                     callback: function(response) {
                        console.log('Response:', response);
              
                    }
                });
          
        });

        frm.add_custom_button(
            __("Check Supliers on Live"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_post.checks.count_supplier.get_updates_supplier_count',
                    callback: function(r) {
                        if (r.message !== null) {
                            var message = `
                                <div>
                                    <strong>Supplier Count:</strong> ${r.message.supplier_count}<br>
                                    
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
            __("Syn Supplier Down"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.supplier_live.get_updates_supplier',
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
