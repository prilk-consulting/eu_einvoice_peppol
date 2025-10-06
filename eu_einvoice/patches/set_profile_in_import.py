import frappe

from eu_einvoice.utils import EInvoiceProfile


def execute():
	for eii in frappe.get_all(
		"E Invoice Import",
		or_filters={
			"correct_european_invoice": 1,
			"correct_german_federal_administration_invoice": 1,
		},
		pluck="name",
	):
		doc = frappe.get_doc("E Invoice Import", eii)

		if doc.correct_german_federal_administration_invoice:
			doc.db_set(
				{
					"profile": EInvoiceProfile.XRECHNUNG.value,
					"e_invoice_is_correct": 1,
				},
				update_modified=False,
			)
		elif doc.correct_european_invoice:
			doc.db_set(
				{
					"profile": EInvoiceProfile.EN16931.value,
					"e_invoice_is_correct": 1,
				},
				update_modified=False,
			)
