# Copyright (c) 2025, Prilk Consulting BV and contributors
"""
PEPPOL Generator

This module provides UBL 2.1 XML generation for PEPPOL BIS Billing 3.0
compliant invoices from ERPNext data.
"""

from lxml import etree as ET
from datetime import datetime
import frappe
from frappe.utils.data import flt

from eu_einvoice.peppol import (
    UBL_NAMESPACES,
    PEPPOL_CUSTOMIZATION_ID,
    PEPPOL_PROFILE_ID,
    uom_codes,
    duty_tax_fee_category_codes,
)

from eu_einvoice.peppol.validator import PEPPOLValidator


class PEPPOLGenerator:
    # Generates PEPPOL BIS Billing 3.0 compliant UBL 2.1 XML documents
    
    namespaces = UBL_NAMESPACES
    
    def __init__(self, invoice):
        # Initialize PEPPOL generator with invoice object
        if not invoice:
            raise ValueError("Invoice is required for PEPPOL generation")

        self.invoice = invoice
        self.xml_string = None
        
        self.seller_address = None
        if invoice.company_address:
            self.seller_address = frappe.get_doc("Address", invoice.company_address)
            
        self.buyer_address = None
        if invoice.customer_address:
            self.buyer_address = frappe.get_doc("Address", invoice.customer_address)
            
        self.shipping_address = None
        if invoice.shipping_address_name:
            self.shipping_address = frappe.get_doc("Address", invoice.shipping_address_name)
            
        self.seller_contact = None
        if invoice.get("company_contact_person"):
            self.seller_contact = frappe.get_doc("Contact", invoice.company_contact_person)
            
        self.buyer_contact = None
        if invoice.contact_person:
            self.buyer_contact = frappe.get_doc("Contact", invoice.contact_person)
    
    def create_einvoice(self):
        # Create the PEPPOL XML document
        try:
            if not self.invoice:
                raise ValueError("No invoice provided to PEPPOLGenerator")

            self.xml_string = self._initialize_document()
            
            self._set_header()
            self._set_seller()
            self._set_buyer()
            self._add_payment_means()
            self._add_allowances_charges()
            self._add_taxes_and_charges()
            self._set_totals()
            self._add_line_items()
            
            self.xml_string = self.finalize_xml_document(self.root)
            
        except Exception as e:
            frappe.logger().error(f"PEPPOL generation failed: {str(e)}")
            import traceback
            frappe.logger().error(f"PEPPOL traceback: {traceback.format_exc()}")
            raise
    
    def _initialize_document(self) -> str:
        # Initialize the UBL 2.1 Invoice XML document
        self.root = self.initialize_peppol_xml()
        return ""
    
    def _set_header(self):
        # Set document header information
        if not hasattr(self, 'root') or self.root is None:
            return
        
        ubl_version = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}UBLVersionID")
        ubl_version.text = '2.1'
        
        customization_id = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}CustomizationID")
        customization_id.text = PEPPOL_CUSTOMIZATION_ID
        
        profile_id = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}ProfileID")
        profile_id.text = PEPPOL_PROFILE_ID
        
        doc_id = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}ID")
        doc_id.text = self.invoice.name
        
        issue_date = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}IssueDate")
        issue_date.text = self.format_date(self.invoice.posting_date)
        
        if self.invoice.due_date:
            due_date = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}DueDate")
            due_date.text = self.format_date(self.invoice.due_date)
        
        invoice_type = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}InvoiceTypeCode")
        invoice_type.text = self.get_invoice_type_code(self.invoice)
        
        currency_code = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}DocumentCurrencyCode")
        currency_code.text = self.invoice.currency
        
        buyer_reference = None
        if self.invoice.buyer_reference:
            buyer_reference = self.invoice.buyer_reference
        elif self.invoice.po_no:
            buyer_reference = self.invoice.po_no

        if buyer_reference:
            buyer_ref = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}BuyerReference")
            buyer_ref.text = buyer_reference
    
    def _set_seller(self):
        # Set seller/supplier information
        if not hasattr(self, 'root') or self.root is None:
            return
        
        supplier_party = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}AccountingSupplierParty")
        party = ET.SubElement(supplier_party, f"{{{self.namespaces['cac']}}}Party")
        
        company = frappe.get_doc("Company", self.invoice.company)
        
        electronic_address = self.get_seller_electronic_address(company, self.seller_contact)
        if electronic_address:
            endpoint = ET.SubElement(party, f"{{{self.namespaces['cbc']}}}EndpointID")
            endpoint.text = electronic_address['value']
            endpoint.set("schemeID", electronic_address['scheme_id'])
        
        party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
        id_elem = ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID")
        id_elem.text = company.name
        
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        name_elem = ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name")
        name_elem.text = company.company_name or company.name
        
        if self.seller_address:
            postal_address = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PostalAddress")
            
            street = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}StreetName")
            street.text = self.seller_address.address_line1 or ""
            
            city = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}CityName")
            city.text = self.seller_address.city or ""
            
            postal_zone = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}PostalZone")
            postal_zone.text = self.seller_address.pincode or ""
            
            country = ET.SubElement(postal_address, f"{{{self.namespaces['cac']}}}Country")
            country_code = ET.SubElement(country, f"{{{self.namespaces['cbc']}}}IdentificationCode")
            if self.seller_address.country:
                country_code.text = (frappe.db.get_value("Country", self.seller_address.country, "code") or "DE").upper()
            else:
                country_code.text = "DE"
        
        if self.invoice.company_tax_id:
            tax_scheme = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            company_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}CompanyID")
            company_id.text = self.invoice.company_tax_id
            
            scheme = ET.SubElement(tax_scheme, f"{{{self.namespaces['cac']}}}TaxScheme")
            scheme_id = ET.SubElement(scheme, f"{{{self.namespaces['cbc']}}}ID")
            scheme_id.text = "VAT"
        
        legal_entity = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyLegalEntity")
        registration_name = ET.SubElement(legal_entity, f"{{{self.namespaces['cbc']}}}RegistrationName")
        registration_name.text = company.company_name or company.name
    
    def _set_buyer(self):
        # Set buyer/customer information
        if not hasattr(self, 'root') or self.root is None:
            return
        
        customer_party = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}AccountingCustomerParty")
        party = ET.SubElement(customer_party, f"{{{self.namespaces['cac']}}}Party")
        
        customer = frappe.get_doc("Customer", self.invoice.customer)
        
        electronic_address = self.get_buyer_electronic_address(customer, self.invoice, self.buyer_contact, self.buyer_address)
        if electronic_address:
            endpoint = ET.SubElement(party, f"{{{self.namespaces['cbc']}}}EndpointID")
            endpoint.text = electronic_address['value']
            endpoint.set("schemeID", electronic_address['scheme_id'])
        
        party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
        id_elem = ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID")
        id_elem.text = customer.name
        
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        name_elem = ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name")
        name_elem.text = customer.customer_name or customer.name
        
        if self.buyer_address:
            postal_address = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PostalAddress")
            
            street = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}StreetName")
            street.text = self.buyer_address.address_line1 or ""
            
            city = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}CityName")
            city.text = self.buyer_address.city or ""
            
            postal_zone = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}PostalZone")
            postal_zone.text = self.buyer_address.pincode or ""
            
            country = ET.SubElement(postal_address, f"{{{self.namespaces['cac']}}}Country")
            country_code = ET.SubElement(country, f"{{{self.namespaces['cbc']}}}IdentificationCode")
            if self.buyer_address.country:
                country_code.text = (frappe.db.get_value("Country", self.buyer_address.country, "code") or "DE").upper()
            else:
                country_code.text = "DE"
        
        if self.invoice.tax_id:
            tax_scheme = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            company_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}CompanyID")
            company_id.text = self.invoice.tax_id
            
            scheme = ET.SubElement(tax_scheme, f"{{{self.namespaces['cac']}}}TaxScheme")
            scheme_id = ET.SubElement(scheme, f"{{{self.namespaces['cbc']}}}ID")
            scheme_id.text = "VAT"
        
        legal_entity = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyLegalEntity")
        registration_name = ET.SubElement(legal_entity, f"{{{self.namespaces['cbc']}}}RegistrationName")
        registration_name.text = customer.customer_name or customer.name
    
    def _add_line_items(self):
        # Add invoice line items
        if not hasattr(self, 'root') or self.root is None:
            return
        
        for item in self.invoice.items:
            self._add_line_item(self.root, item)
    
    def _add_line_item(self, root: ET.Element, item):
        # Add a single line item
        invoice_line = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}InvoiceLine")
        
        line_id = ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}ID")
        line_id.text = str(item.idx)
        
        quantity = ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}InvoicedQuantity")
        quantity.text = str(flt(item.qty, item.precision("qty")))
        quantity.set("unitCode", self.map_unit_code(item.uom))
        
        line_amount = ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}LineExtensionAmount")
        line_amount.text = str(flt(item.amount, item.precision("amount")))
        line_amount.set("currencyID", self.invoice.currency)
        
        item_elem = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}Item")
        
        description = ET.SubElement(item_elem, f"{{{self.namespaces['cbc']}}}Description")
        description.text = item.description or item.item_name
        
        name = ET.SubElement(item_elem, f"{{{self.namespaces['cbc']}}}Name")
        name.text = item.item_name
        
        tax_category = ET.SubElement(item_elem, f"{{{self.namespaces['cac']}}}ClassifiedTaxCategory")
        
        category_id = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID")
        category_id.text = "S"
        
        item_tax_rate = self._get_item_tax_rate(item)
        tax_percent = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent")
        tax_percent.text = str(flt(item_tax_rate or 0, 2))
        
        tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
        scheme_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID")
        scheme_id.text = "VAT"
        
        price = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}Price")
        price_amount = ET.SubElement(price, f"{{{self.namespaces['cbc']}}}PriceAmount")
        price_amount.text = str(flt(item.rate, item.precision("rate")))
        price_amount.set("currencyID", self.invoice.currency)
    
    def _add_taxes_and_charges(self):
        # Add taxes and charges using ERPNext totals directly
        if not hasattr(self, 'root') or self.root is None:
            return
        
        tax_total = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}TaxTotal")
        
        tax_total_amount = sum(tax.tax_amount for tax in self.invoice.taxes if tax.charge_type != "Actual")
        
        tax_amount = ET.SubElement(tax_total, f"{{{self.namespaces['cbc']}}}TaxAmount")
        tax_amount.text = str(flt(tax_total_amount, 2))
        tax_amount.set("currencyID", self.invoice.currency)
        
        # Aggregate taxes by rate, handling both item-level and invoice-level taxes
        tax_rates = {}

        # Iterate through items to get their applicable tax rates
        for item in self.invoice.items:
            rate = self._get_item_tax_rate(item)

            if not rate or rate == 0:
                continue

            if rate not in tax_rates:
                tax_rates[rate] = {
                    'amount': 0,
                    'taxable_amount': 0
                }

            # Calculate tax amount for this item
            tax_amount = flt(item.net_amount) * rate / 100
            tax_rates[rate]['amount'] += tax_amount
            tax_rates[rate]['taxable_amount'] += flt(item.net_amount)
        
        for rate, data in tax_rates.items():
            tax_subtotal = ET.SubElement(tax_total, f"{{{self.namespaces['cac']}}}TaxSubtotal")
            
            taxable_amount = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxableAmount")
            taxable_amount.text = str(flt(data['taxable_amount'], 2))
            taxable_amount.set("currencyID", self.invoice.currency)
            
            tax_amount = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxAmount")
            tax_amount.text = str(flt(data['amount'], 2))
            tax_amount.set("currencyID", self.invoice.currency)
            
            tax_category = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cac']}}}TaxCategory")
            
            category_id = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID")
            category_id.text = "S"
            
            tax_percent = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent")
            tax_percent.text = str(flt(rate, 2))
            
            tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
            scheme_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID")
            scheme_id.text = "VAT"
            
    def _add_payment_means(self):
        # Add payment means information
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # Add PaymentMeans
        payment_means = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}PaymentMeans")
        
        # Payment Means Code 
        payment_code = ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentMeansCode")
        payment_code.text = "1"
        
        if hasattr(self.invoice, 'payment_reference') and self.invoice.payment_reference:
            payment_id = ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentID")
            payment_id.text = self.invoice.payment_reference
        
        # Payee Financial Account (if company has bank details)
        if hasattr(self.invoice, 'mode_of_payment') and self.invoice.mode_of_payment:
            try:
                mode_of_payment = frappe.get_doc("Mode of Payment", self.invoice.mode_of_payment)
                if mode_of_payment.type == "Bank":
                    # Get bank account details
                    bank_account = frappe.db.get_value(
                        "Mode of Payment Account", 
                        {"parent": self.invoice.mode_of_payment, "company": self.invoice.company}, 
                        "default_account"
                    )
                    
                    if bank_account:
                        payee_financial_account = ET.SubElement(payment_means, f"{{{self.namespaces['cac']}}}PayeeFinancialAccount")
                        financial_account_id = ET.SubElement(payee_financial_account, f"{{{self.namespaces['cbc']}}}ID")
                        financial_account_id.text = bank_account
                        
                        # Get bank details
                        bank_account_doc = frappe.get_doc("Bank Account", {"account": bank_account, "company": self.invoice.company})
                        if bank_account_doc:
                            financial_institution = ET.SubElement(payee_financial_account, f"{{{self.namespaces['cac']}}}FinancialInstitution")
                            financial_institution_id = ET.SubElement(financial_institution, f"{{{self.namespaces['cbc']}}}ID")
                            financial_institution_id.text = bank_account_doc.bank or ""
                            
                            # Bank name
                            if bank_account_doc.bank:
                                bank_doc = frappe.get_doc("Bank", bank_account_doc.bank)
                                financial_institution_name = ET.SubElement(financial_institution, f"{{{self.namespaces['cbc']}}}Name")
                                financial_institution_name.text = bank_doc.bank_name or bank_doc.name
            except Exception:
                pass
    
    def _add_allowances_charges(self):
        # Add document-level allowances and charges
        if not hasattr(self, 'root') or self.root is None:
            return
        
        has_allowances_charges = False
        for tax in self.invoice.taxes:
            if tax.charge_type == "Actual" and tax.tax_amount != 0:
                has_allowances_charges = True
                break
        
        if not has_allowances_charges:
            return
        
        for tax in self.invoice.taxes:
            if tax.charge_type == "Actual" and tax.tax_amount != 0:
                allowance_charge = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}AllowanceCharge")
                
                charge_indicator = ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}ChargeIndicator")
                charge_indicator.text = "true"
                
                if tax.description:
                    reason = ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}AllowanceChargeReason")
                    reason.text = tax.description
                
                # Amount
                amount = ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}Amount")
                amount.text = str(flt(tax.tax_amount, 2))
                amount.set("currencyID", self.invoice.currency)
                
                # Tax Category (if applicable)
                if tax.rate and tax.rate > 0:
                    tax_category = ET.SubElement(allowance_charge, f"{{{self.namespaces['cac']}}}TaxCategory")
                    
                    # Category ID
                    category_id = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID")
                    category_id.text = "S"
                    
                    tax_percent = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent")
                    tax_percent.text = str(flt(tax.rate, 2))
                    
                    # Tax scheme
                    tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
                    scheme_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID")
                    scheme_id.text = "VAT"
    
    def _set_totals(self):
        # Set monetary totals using ERPNext values directly
        if not hasattr(self, 'root') or self.root is None:
            return
            
        # Add LegalMonetaryTotal section
        legal_total = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}LegalMonetaryTotal")
        
        # Line Extension Amount Sum of Invoice line net amount
        line_total = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}LineExtensionAmount")
        line_total.text = str(flt(self.invoice.net_total, 2))
        line_total.set("currencyID", self.invoice.currency)
        
        # Calculate actual charges 
        actual_charge_total = sum(tax.tax_amount for tax in self.invoice.taxes if tax.charge_type == "Actual")
        if actual_charge_total:
            charge_total = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}ChargeTotalAmount")
            charge_total.text = str(flt(actual_charge_total, 2))
            charge_total.set("currencyID", self.invoice.currency)
        
        # Tax Exclusive Amount Invoice total amount without VAT
        tax_exclusive_amount = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}TaxExclusiveAmount")
        tax_exclusive_amount.text = str(flt(self.invoice.net_total + actual_charge_total, 2))
        tax_exclusive_amount.set("currencyID", self.invoice.currency)
        
        
        # Tax Inclusive Amount (BT-112) - Invoice total amount with VAT
        tax_inclusive_amount = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}TaxInclusiveAmount")
        tax_inclusive_amount.text = str(flt(self.invoice.grand_total, 2))
        tax_inclusive_amount.set("currencyID", self.invoice.currency)
        
        # Allowance Total Amount (BT-107) - Sum of allowances on document level
        allowance_total = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}AllowanceTotalAmount")
        allowance_total.text = "0.00"
        allowance_total.set("currencyID", self.invoice.currency)
        
        # Payable Amount (BT-112) - Amount due for payment
        payable_amount = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}PayableAmount")
        payable_amount.text = str(flt(self.invoice.outstanding_amount, 2))
        payable_amount.set("currencyID", self.invoice.currency)
    
    def initialize_peppol_xml(self) -> ET.Element:
        # Initialize the PEPPOL XML document with root element and namespaces
        root = ET.Element('{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice')
        
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
            
        return root
    
    def finalize_xml_document(self, root: ET.Element) -> str:
        # Format XML and return as string
        xml_bytes = ET.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)
        return xml_bytes.decode('utf-8')


    def format_date(self, date):
        # Format date to YYYY-MM-DD string
        if not date:
            return None
        
        try:
            if isinstance(date, str):
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                return date
            
            if hasattr(date, 'strftime'):
                return date.strftime('%Y-%m-%d')
            
            return str(date)
            
        except Exception as e:
            frappe.logger().error(f"Error formatting date {date} (type: {type(date)}): {str(e)}")
            return str(date) if date else None

    def _get_item_tax_rate(self, item) -> float | None:
        # Get the tax rate for an item from the item tax template and the taxes table
        if item.item_tax_template:
            tax_template = frappe.get_doc("Item Tax Template", item.item_tax_template)
            applicable_accounts = [tax.account_head for tax in self.invoice.taxes if tax.account_head]

            for item_tax in tax_template.taxes:
                if item_tax.tax_type in applicable_accounts:
                    return item_tax.tax_rate

        tax_rates = [invoice_tax.rate for invoice_tax in self.invoice.taxes if invoice_tax.charge_type == "On Net Total"]
        return tax_rates[0] if len(tax_rates) == 1 else None
    
    def get_seller_electronic_address(self, company, seller_contact=None) -> dict[str, str] | None:
        # Get seller electronic address
        if company.electronic_address_scheme and company.electronic_address:
            scheme_id = frappe.db.get_value("Common Code", company.electronic_address_scheme, "common_code")
            if scheme_id:
                return {'value': company.electronic_address, 'scheme_id': scheme_id}

        electronic_address = None
        if seller_contact and seller_contact.email_id:
            electronic_address = seller_contact.email_id
        else:
            electronic_address = company.email

        if electronic_address:
            return {'value': electronic_address, 'scheme_id': 'EM'}

        return None

    def get_buyer_electronic_address(self, customer, invoice, buyer_contact=None, buyer_address=None) -> dict[str, str] | None:
        # Get buyer electronic address
        if customer.electronic_address_scheme and customer.electronic_address:
            scheme_id = frappe.db.get_value("Common Code", customer.electronic_address_scheme, "common_code")
            if scheme_id:
                return {'value': customer.electronic_address, 'scheme_id': scheme_id}

        electronic_address = None
        if invoice.contact_email:
            electronic_address = invoice.contact_email
        elif buyer_address and buyer_address.email_id:
            electronic_address = buyer_address.email_id

        if electronic_address:
            return {'value': electronic_address, 'scheme_id': 'EM'}

        return None
    
    def get_invoice_type_code(self, invoice) -> str:
        # Determine the appropriate PEPPOL invoice type code
        invoice_type_code = '380'
        
        try:
            if hasattr(invoice, 'is_return') and invoice.is_return:
                invoice_type_code = '381'
            elif hasattr(invoice, 'amended_from') and invoice.amended_from:
                invoice_type_code = '384'
        except Exception:
            pass
        
        return invoice_type_code

    def map_unit_code(self, erpnext_unit: str) -> str:
        # Map ERPNext unit codes to PEPPOL standard unit codes using CommonCodeRetriever
        if not erpnext_unit:
            return uom_codes.default_code or 'C62'

        return uom_codes.get([("UOM", erpnext_unit)]) or uom_codes.default_code or 'C62'

    def get_vat_category_code(self, invoice, item=None, tax=None) -> str:
        # Get VAT category code using CommonCodeRetriever
        lookup_records = []

        if item:
            lookup_records.extend([
                ("Item Tax Template", getattr(item, 'item_tax_template', None)),
                ("Account", getattr(item, 'income_account', None)),
            ])

        if tax:
            # For tax-level VAT category (BT-118)
            lookup_records.extend([
                ("Account", getattr(tax, 'account_head', None)),
            ])

        lookup_records.extend([
            ("Tax Category", getattr(invoice, 'tax_category', None)),
            ("Sales Taxes and Charges Template", getattr(invoice, 'taxes_and_charges', None)),
        ])

        lookup_records = [(doctype, name) for doctype, name in lookup_records if name]

        # Get the VAT category code using CommonCodeRetriever (same as EInvoiceGenerator)
        category_code = duty_tax_fee_category_codes.get(lookup_records)

        return category_code

    def get_xml_string(self) -> str:
        # Return the XML as a string
        if not self.xml_string:
            raise ValueError("No XML generated. Call create_einvoice() first.")
        return self.xml_string
    
    def get_xml_bytes(self) -> bytes:
        # Return the XML as bytes
        if not self.xml_string:
            raise ValueError("No XML generated. Call create_einvoice() first.")
        return self.xml_string.encode('utf-8')