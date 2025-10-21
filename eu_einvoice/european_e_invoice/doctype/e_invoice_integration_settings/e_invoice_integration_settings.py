# Copyright (c) 2025, ALYF GmbH and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EInvoiceIntegrationSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_id: DF.Data | None
		api_key: DF.Data | None
		api_secret: DF.Data | None
		base_url: DF.Data | None
		company: DF.Link | None
		company_id: DF.Data | None
		einvoice_integrator: DF.Literal["B2B Router", "Recommand"]
		einvoice_profile: DF.Literal["", "BASIC", "EN16931", "EXTENDED", "XRECHNUNG", "PEPPOL"]
	# end: auto-generated types

	pass
