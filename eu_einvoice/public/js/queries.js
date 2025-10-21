frappe.provide("eu_einvoice.queries");

eu_einvoice.queries = {
	electronic_address_scheme: function (doc) {
		console.log("Electronic Address Scheme filter called");
		return {
			filters: {
				code_list: [
					"in",
					[
						"urn:xoev-de:kosit:codeliste:eas",     // XRechnung
						"urn:cef.eu:names:identifier:EAS",     // EN 16931
						"urn:peppol:id:codelist:eas",         // PEPPOL
					],
				],
			},
		};
	},
};
