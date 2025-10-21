frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		frm.trigger("add_einvoice_button");

		if (!frm.is_dirty() && !frm.doc.einvoice_is_correct && frm.doc.einvoice_profile) {
			frm.dashboard.set_headline_alert(
				__("Please note the validation errors of the e-invoice.")
			);
		}
	},
	add_einvoice_button: function (frm) {
		if (frm.is_new() || !frm.doc.einvoice_profile) {
			return;
		}

		// Download eInvoice option
		frm.page.add_menu_item(__("Download eInvoice"), () => {
			window.open(
				`/api/method/eu_einvoice.european_e_invoice.custom.sales_invoice.download_xrechnung?invoice_id=${encodeURIComponent(
					frm.doc.name
				)}`,
				"_blank"
			);
		});

		// Send eInvoice via API option (only for PEPPOL profiles)
		if (frm.doc.einvoice_profile === "PEPPOL") {
			frm.page.add_menu_item(__("Send eInvoice via API"), () => {
				frappe.confirm(
					__("Are you sure you want to transmit this invoice to Peppol Netwrok?"),
					() => {
						// Show loading indicator
						frappe.show_progress(__("Transmitting..."), 0, 100, __("Sending invoice to Peppol Netwrok"));

						// Call the API
						frappe.call({
							method: "eu_einvoice.api.transmit_e_invoice",
							args: {
								invoice_name: frm.doc.name
							},
							callback: function(r) {
								frappe.hide_progress();

								if (r.message) {
									if (r.message.status === "success") {
										frappe.show_alert({
											message: r.message.message,
											indicator: 'green'
										});

										// Refresh the form to show updated transmission details
										frm.reload_doc();
									} else {
										frappe.show_alert({
											message: r.message.message,
											indicator: 'red'
										});
									}
								}
							},
							error: function(r) {
								frappe.hide_progress();
								frappe.show_alert({
									message: __("Transmission failed. Please check the logs for details."),
									indicator: 'red'
								});
							}
						});
					}
				);
			});
		}
	},
});
