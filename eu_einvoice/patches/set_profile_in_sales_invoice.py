import frappe

from eu_einvoice.utils import EInvoiceProfile


def execute():
	for si in frappe.get_all(
		"Sales Invoice",
		or_filters={
			"correct_european_invoice": 1,
			"correct_german_federal_administration_invoice": 1,
		},
		pluck="name",
	):
		doc = frappe.get_doc("Sales Invoice", si)

		if doc.correct_german_federal_administration_invoice:
			doc.db_set(
				{
					"einvoice_profile": EInvoiceProfile.XRECHNUNG.value,
					"einvoice_is_correct": 1,
				},
				update_modified=False,
			)
		elif doc.correct_european_invoice:
			doc.db_set(
				{
					"einvoice_profile": EInvoiceProfile.EN16931.value,
					"einvoice_is_correct": 1,
				},
				update_modified=False,
			)

	frappe.delete_doc_if_exists("Custom Field", "Sales Invoice-correct_german_federal_administration_invoice")
	frappe.delete_doc_if_exists("Custom Field", "Sales Invoice-correct_european_invoice")
