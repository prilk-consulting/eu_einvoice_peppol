// Copyright (c) 2025, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("E Invoice Settings", {
	refresh: function(frm) {
		// Add button to import PEPPOL code lists
		frm.add_custom_button(__("Setup PEPPOL Code Lists"), function() {
			frappe.confirm(
				__("This will import all PEPPOL code lists and create Common Code entries. This may take a few minutes. Continue?"),
				function() {
					frappe.call({
						method: "eu_einvoice.peppol.setup_peppol_codes.setup_peppol_codes",
						freeze: true,
						freeze_message: __("Importing PEPPOL code lists..."),
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({
									message: __("PEPPOL code lists imported successfully"),
									indicator: "green"
								});
								frappe.msgprint({
									title: __("Success"),
									message: __("PEPPOL code lists have been imported successfully. You can now use PEPPOL profiles for e-invoicing."),
									indicator: "green"
								});
							}
						}
					});
				}
			);
		}, __("Setup"));
	}
});
