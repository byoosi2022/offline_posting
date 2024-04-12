frappe.ui.form.on('Offline Sync', {
    refresh: function(frm) {

        frm.add_custom_button(
            __("Check Unsynced Data"),
            function () {
                frappe.call({
                    method: 'offline_posting.custom_api.offline_sync.insert_invpoice_post',
                    args: { doc: frm.doc, document_type: frm.doc.document_type },
                    callback: function(r) {
                        console.log(r);
                        if (r.message !== null) {
                            frappe.msgprint(__('Unsynced Data Count: {0}', [r.message]));
                            console.log(r.message);
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
                        console.log(response);
                        // Handle the response here
                    }
                });
                
            },
            __("Sync Data")
        );
        
    }
});
