// PEPPOL Client Script for Sales Invoice
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        // Only show PEPPOL buttons if the invoice is configured for PEPPOL
        if (frm.doc.einvoice_profile === 'PEPPOL') {
            // Add Download PEPPOL XML button
            frm.add_custom_button(__('Download PEPPOL XML'), function() {
                frappe.call({
                    method: 'eu_einvoice.european_e_invoice.custom.sales_invoice.download_peppol',
                    args: {
                        invoice_id: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.exc) {
                            frappe.msgprint(__('Error downloading PEPPOL XML: ') + r.exc);
                        }
                    }
                });
            }, __('E-Invoice'));

            // Add Save PEPPOL XML button
            frm.add_custom_button(__('Save PEPPOL XML'), function() {
                frappe.call({
                    method: 'eu_einvoice.european_e_invoice.custom.sales_invoice.save_peppol_xml',
                    args: {
                        invoice_id: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.exc) {
                            frappe.msgprint(__('Error saving PEPPOL XML: ') + r.exc);
                        } else {
                            frappe.msgprint(__('PEPPOL XML saved successfully'));
                            frm.reload_doc();
                        }
                    }
                });
            }, __('E-Invoice'));

            // Add View PEPPOL XML button
            frm.add_custom_button(__('View PEPPOL XML'), function() {
                frappe.call({
                    method: 'eu_einvoice.european_e_invoice.custom.sales_invoice.get_peppol_xml_content',
                    args: {
                        invoice_id: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.exc) {
                            frappe.msgprint(__('Error getting PEPPOL XML: ') + r.exc);
                        } else {
                            // Show XML content in a dialog
                            let d = new frappe.ui.Dialog({
                                title: __('PEPPOL XML Content'),
                                size: 'large',
                                fields: [{
                                    fieldtype: 'Code',
                                    fieldname: 'xml_content',
                                    label: __('XML Content'),
                                    default: r.message,
                                    options: 'xml',
                                    read_only: 1
                                }]
                            });
                            d.show();
                        }
                    }
                });
            }, __('E-Invoice'));
        }
    }
}); 