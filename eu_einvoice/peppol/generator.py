"""
PEPPOL Generator

This module provides UBL 2.1 XML generation for PEPPOL BIS Billing 3.0
compliant invoices from ERPNext data.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from datetime import datetime
import frappe
from frappe.utils.data import flt

from eu_einvoice.common_codes import CommonCodeRetriever

# PEPPOL BIS Billing 3.0 Constants
PEPPOL_CUSTOMIZATION_ID = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
PEPPOL_PROFILE_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

# Global code retrievers for PEPPOL standardized codes (following EInvoiceGenerator pattern)
duty_tax_fee_category_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNCL5305"], "S")
uom_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNECERec20"], "C62")
payment_means_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNCL4461"], "ZZZ")
country_codes = CommonCodeRetriever(["urn:peppol:id:codelist:ISO3166-1_Alpha2"], "DE")
currency_codes = CommonCodeRetriever(["urn:peppol:id:codelist:ISO4217"], "EUR")
electronic_address_schemes = CommonCodeRetriever(["urn:peppol:id:codelist:eas"], "EM")


class PEPPOLGenerator:
    """Generates PEPPOL BIS Billing 3.0 compliant UBL 2.1 XML documents."""
    
    # UBL namespaces (constant)
    namespaces = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        }
    
    
    def __init__(self, invoice):
        """Initialize PEPPOL generator with invoice object."""
        if not invoice:
            raise ValueError("Invoice is required for PEPPOL generation")

        self.invoice = invoice
        self.xml_string = None
        
        # Fetch related entities internally (same as E-Invoice core approach)
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
    
    # ============================================================================
    # MAIN WORKFLOW METHODS
    # ============================================================================
    
    def create_einvoice(self):
        """Create the PEPPOL XML document."""
        try:
            if not self.invoice:
                raise ValueError("No invoice provided to PEPPOLGenerator")

            # Initialize XML document
            self.xml_string = self._initialize_document()
            
            # Add document sections in correct UBL 2.1 order
            self._set_header()
            self._set_seller()
            self._set_buyer()
            self._add_payment_means()
            self._add_allowances_charges()
            self._add_taxes_and_charges()
            self._set_totals()
            self._add_line_items()  # MUST BE LAST according to UBL 2.1 XSD
            
            # Finalize the XML document
            self.xml_string = self.finalize_xml_document(self.root)
            
        except Exception as e:
            frappe.logger().error(f"PEPPOL generation failed: {str(e)}")
            import traceback
            frappe.logger().error(f"PEPPOL traceback: {traceback.format_exc()}")
            raise
    
    def _initialize_document(self) -> str:
        """Initialize the UBL 2.1 Invoice XML document."""
        # Create the root element
        self.root = self.initialize_peppol_xml()
        # Return empty string initially - will be finalized at the end
        return ""
    
    def _set_header(self):
        """Set document header information (aligned with E-Invoice core)."""
        # Use the root element directly
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # UBL Version ID (must come early according to XSD schema)
        ubl_version = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}UBLVersionID")
        ubl_version.text = '2.1'
        
        # Customization ID (BT-24)
        customization_id = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}CustomizationID")
        customization_id.text = PEPPOL_CUSTOMIZATION_ID
        
        # Profile ID (BT-23)
        profile_id = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}ProfileID")
        profile_id.text = PEPPOL_PROFILE_ID
        
        # Document ID
        doc_id = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}ID")
        doc_id.text = self.invoice.name
        
        # Issue Date
        issue_date = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}IssueDate")
        issue_date.text = self.format_date(self.invoice.posting_date)
        
        # Due Date
        if self.invoice.due_date:
            due_date = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}DueDate")
            due_date.text = self.format_date(self.invoice.due_date)
        
        # Invoice Type Code
        invoice_type = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}InvoiceTypeCode")
        invoice_type.text = self.get_invoice_type_code(self.invoice)
        
        # Document Currency Code
        currency_code = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}DocumentCurrencyCode")
        currency_code.text = self.invoice.currency
        
        # Buyer Reference (required for PEPPOL)
        buyer_reference = None
        if self.invoice.buyer_reference:
            buyer_reference = self.invoice.buyer_reference
        elif self.invoice.po_no:
            buyer_reference = self.invoice.po_no

        if buyer_reference:
            buyer_ref = ET.SubElement(self.root, f"{{{self.namespaces['cbc']}}}BuyerReference")
            buyer_ref.text = buyer_reference
    
    def _set_seller(self):
        """Set seller/supplier information (aligned with E-Invoice core)."""
        # Use the root element directly
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # Add AccountingSupplierParty
        supplier_party = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}AccountingSupplierParty")
        party = ET.SubElement(supplier_party, f"{{{self.namespaces['cac']}}}Party")
        
        # Get company information
        company = frappe.get_doc("Company", self.invoice.company)
        
        # Electronic Address (required for PEPPOL) - must be first in Party sequence
        electronic_address = self.get_seller_electronic_address(company, self.seller_contact)
        if electronic_address:
            endpoint = ET.SubElement(party, f"{{{self.namespaces['cbc']}}}EndpointID")
            endpoint.text = electronic_address['value']
            endpoint.set("schemeID", electronic_address['scheme_id'])
        
        # Party Identification
        party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
        id_elem = ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID")
        id_elem.text = company.name
        
        # Party Name
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        name_elem = ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name")
        name_elem.text = company.company_name or company.name
        
        # Postal Address
        if self.seller_address:
            postal_address = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PostalAddress")
            
            # Street Name
            street = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}StreetName")
            street.text = self.seller_address.address_line1 or ""
            
            # City Name
            city = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}CityName")
            city.text = self.seller_address.city or ""
            
            # Postal Zone
            postal_zone = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}PostalZone")
            postal_zone.text = self.seller_address.pincode or ""
            
            # Country
            country = ET.SubElement(postal_address, f"{{{self.namespaces['cac']}}}Country")
            country_code = ET.SubElement(country, f"{{{self.namespaces['cbc']}}}IdentificationCode")
            # Use same approach as E-Invoice core: get country code from Country doctype
            if self.seller_address.country:
                country_code.text = (frappe.db.get_value("Country", self.seller_address.country, "code") or "DE").upper()
            else:
                country_code.text = "DE"
        
        # Party Tax Scheme (use same field as E-Invoice core)
        if self.invoice.company_tax_id:
            tax_scheme = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            company_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}CompanyID")
            company_id.text = self.invoice.company_tax_id
            
            scheme = ET.SubElement(tax_scheme, f"{{{self.namespaces['cac']}}}TaxScheme")
            scheme_id = ET.SubElement(scheme, f"{{{self.namespaces['cbc']}}}ID")
            scheme_id.text = "VAT"
        
        # Party Legal Entity
        legal_entity = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyLegalEntity")
        registration_name = ET.SubElement(legal_entity, f"{{{self.namespaces['cbc']}}}RegistrationName")
        registration_name.text = company.company_name or company.name
    
    def _set_buyer(self):
        """Set buyer/customer information (aligned with E-Invoice core)."""
        # Use the root element directly
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # Add AccountingCustomerParty
        customer_party = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}AccountingCustomerParty")
        party = ET.SubElement(customer_party, f"{{{self.namespaces['cac']}}}Party")
        
        # Get customer information
        customer = frappe.get_doc("Customer", self.invoice.customer)
        
        # Electronic Address (required for PEPPOL) - must be first in Party sequence
        electronic_address = self.get_buyer_electronic_address(customer, self.invoice, self.buyer_contact, self.buyer_address)
        if electronic_address:
            endpoint = ET.SubElement(party, f"{{{self.namespaces['cbc']}}}EndpointID")
            endpoint.text = electronic_address['value']
            endpoint.set("schemeID", electronic_address['scheme_id'])
        
        # Party Identification
        party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
        id_elem = ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID")
        id_elem.text = customer.name
        
        # Party Name
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        name_elem = ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name")
        name_elem.text = customer.customer_name or customer.name
        
        # Postal Address
        if self.buyer_address:
            postal_address = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PostalAddress")
            
            # Street Name
            street = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}StreetName")
            street.text = self.buyer_address.address_line1 or ""
            
            # City Name
            city = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}CityName")
            city.text = self.buyer_address.city or ""
            
            # Postal Zone
            postal_zone = ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}PostalZone")
            postal_zone.text = self.buyer_address.pincode or ""
            
            # Country
            country = ET.SubElement(postal_address, f"{{{self.namespaces['cac']}}}Country")
            country_code = ET.SubElement(country, f"{{{self.namespaces['cbc']}}}IdentificationCode")
            # Use same approach as E-Invoice core: get country code from Country doctype
            if self.buyer_address.country:
                country_code.text = (frappe.db.get_value("Country", self.buyer_address.country, "code") or "DE").upper()
            else:
                country_code.text = "DE"
        
        # Party Tax Scheme (use same field as E-Invoice core)
        if self.invoice.tax_id:
            tax_scheme = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            company_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}CompanyID")
            company_id.text = self.invoice.tax_id
            
            scheme = ET.SubElement(tax_scheme, f"{{{self.namespaces['cac']}}}TaxScheme")
            scheme_id = ET.SubElement(scheme, f"{{{self.namespaces['cbc']}}}ID")
            scheme_id.text = "VAT"
        
        # Party Legal Entity
        legal_entity = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyLegalEntity")
        registration_name = ET.SubElement(legal_entity, f"{{{self.namespaces['cbc']}}}RegistrationName")
        registration_name.text = customer.customer_name or customer.name
    
    def _add_line_items(self):
        """Add invoice line items (aligned with E-Invoice core)."""
        # Use the root element directly
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # Process each line item (similar to E-Invoice core _add_line_item)
        for item in self.invoice.items:
            self._add_line_item(self.root, item)
    
    def _add_line_item(self, root: ET.Element, item):
        """Add a single line item (aligned with E-Invoice core approach)."""
        # Create InvoiceLine element
        invoice_line = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}InvoiceLine")
        
        # Line ID
        line_id = ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}ID")
        line_id.text = str(item.idx)
        
        # Invoiced Quantity
        quantity = ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}InvoicedQuantity")
        quantity.text = str(flt(item.qty, item.precision("qty")))
        quantity.set("unitCode", self.map_unit_code(item.uom))
        
        # Line Extension Amount
        line_amount = ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}LineExtensionAmount")
        line_amount.text = str(flt(item.amount, item.precision("amount")))
        line_amount.set("currencyID", self.invoice.currency)
        
        # Item information
        item_elem = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}Item")
        
        # Item description
        description = ET.SubElement(item_elem, f"{{{self.namespaces['cbc']}}}Description")
        description.text = item.description or item.item_name
        
        # Item name
        name = ET.SubElement(item_elem, f"{{{self.namespaces['cbc']}}}Name")
        name.text = item.item_name
        
        # Classified Tax Category
        tax_category = ET.SubElement(item_elem, f"{{{self.namespaces['cac']}}}ClassifiedTaxCategory")
        
        # Tax category ID (use CommonCodeRetriever like E-Invoice core)
        category_id = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID")
        category_id.text = "S"  # Standard rate (can be enhanced with CommonCodeRetriever)
        
        # Tax percentage - use same approach as E-Invoice core
        item_tax_rate = self._get_item_tax_rate(item)
        tax_percent = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent")
        tax_percent.text = str(flt(item_tax_rate or 0, 2))
        
        # Tax scheme
        tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
        scheme_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID")
        scheme_id.text = "VAT"
        
        # Price information
        price = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}Price")
        price_amount = ET.SubElement(price, f"{{{self.namespaces['cbc']}}}PriceAmount")
        price_amount.text = str(flt(item.rate, item.precision("rate")))
        price_amount.set("currencyID", self.invoice.currency)
    
    def _add_taxes_and_charges(self):
        """Add taxes and charges using ERPNext totals directly (aligned with E-Invoice core)."""
        # Use the root element directly
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # Add TaxTotal section
        tax_total = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}TaxTotal")
        
        # Calculate tax total from ERPNext taxes (same as E-Invoice core)
        tax_total_amount = sum(tax.tax_amount for tax in self.invoice.taxes if tax.charge_type != "Actual")
        
        # Tax Amount
        tax_amount = ET.SubElement(tax_total, f"{{{self.namespaces['cbc']}}}TaxAmount")
        tax_amount.text = str(flt(tax_total_amount, 2))
        tax_amount.set("currencyID", self.invoice.currency)
        
        # Add TaxSubtotal for each tax rate
        tax_rates = {}
        for tax in self.invoice.taxes:
            if tax.charge_type != "Actual" and tax.tax_amount > 0:
                rate = tax.rate or 0
                if rate not in tax_rates:
                    tax_rates[rate] = {
                        'amount': 0,
                        'taxable_amount': 0
                    }
                tax_rates[rate]['amount'] += tax.tax_amount
                
                # Calculate taxable amount using same logic as E-Invoice core
                if len(self.invoice.taxes) == 1:
                    # We only have one tax, so we can use the net total as basis amount
                    tax_rates[rate]['taxable_amount'] += self.invoice.net_total
                elif hasattr(tax, "net_amount"):
                    tax_rates[rate]['taxable_amount'] += tax.net_amount
                elif hasattr(tax, "custom_net_amount"):
                    tax_rates[rate]['taxable_amount'] += tax.custom_net_amount
                elif tax.tax_amount and rate:
                    # We don't know the basis amount for this tax, so we try to calculate it
                    tax_rates[rate]['taxable_amount'] += round(tax.tax_amount / rate * 100, 2)
                else:
                    tax_rates[rate]['taxable_amount'] += 0
        
        # Create TaxSubtotal for each rate
        for rate, data in tax_rates.items():
            tax_subtotal = ET.SubElement(tax_total, f"{{{self.namespaces['cac']}}}TaxSubtotal")
            
            # Taxable Amount
            taxable_amount = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxableAmount")
            taxable_amount.text = str(flt(data['taxable_amount'], 2))
            taxable_amount.set("currencyID", self.invoice.currency)
            
            # Tax Amount
            tax_amount = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxAmount")
            tax_amount.text = str(flt(data['amount'], 2))
            tax_amount.set("currencyID", self.invoice.currency)
            
            # Tax Category
            tax_category = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cac']}}}TaxCategory")
            
            # Category ID
            category_id = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID")
            category_id.text = "S"  # Standard rate
            
            # Tax percentage
            tax_percent = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent")
            tax_percent.text = str(flt(rate, 2))
            
            # Tax scheme
            tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
            scheme_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID")
            scheme_id.text = "VAT"
        
        # Update the XML string
        # No need to update xml_string here - it's set at the end of create_einvoice()
    
    def _add_payment_means(self):
        """Add payment means information (aligned with E-Invoice core)."""
        # Use the root element directly
        if not hasattr(self, 'root') or self.root is None:
            return
        
        # Add PaymentMeans
        payment_means = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}PaymentMeans")
        
        # Payment Means Code (default to 1 = Bank transfer)
        payment_code = ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentMeansCode")
        payment_code.text = "1"  # Bank transfer
        
        # Payment Due Date - removed per UBL-CR-412 (not allowed in PaymentMeans)
        
        # Payment ID (if available)
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
                # If bank details are not available, continue without them
                pass
        
        # Update the XML string
        # No need to update xml_string here - it's set at the end of create_einvoice()
    
    def _add_allowances_charges(self):
        """Add document-level allowances and charges (aligned with E-Invoice core)."""
        # Parse the current XML to get the root element
        if not self.xml_string:
            return
            
        try:
            root = ET.fromstring(self.xml_string)
        except ET.ParseError:
            return
        
        # Check if there are any allowances or charges in the invoice
        has_allowances_charges = False
        
        # Check for document-level allowances/charges in ERPNext taxes
        for tax in self.invoice.taxes:
            if tax.charge_type == "Actual" and tax.tax_amount != 0:
                has_allowances_charges = True
                break
        
        if not has_allowances_charges:
            return
        
        # Add AllowanceCharge elements for each document-level charge
        for tax in self.invoice.taxes:
            if tax.charge_type == "Actual" and tax.tax_amount != 0:
                allowance_charge = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}AllowanceCharge")
                
                # Charge Indicator (true for charges, false for allowances)
                charge_indicator = ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}ChargeIndicator")
                charge_indicator.text = "true"  # Assuming charges for now
                
                # Allowance Charge Reason
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
                    category_id.text = "S"  # Standard rate
                    
                    # Tax percentage
                    tax_percent = ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent")
                    tax_percent.text = str(flt(tax.rate, 2))
                    
                    # Tax scheme
                    tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
                    scheme_id = ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID")
                    scheme_id.text = "VAT"
        
        # Update the XML string
        # No need to update xml_string here - it's set at the end of create_einvoice()
    
    def _set_totals(self):
        """Set monetary totals using ERPNext values directly (aligned with E-Invoice core)."""
        # Use ERPNext totals directly instead of re-calculating
        # This follows the same pattern as E-Invoice core _set_totals method
        
        # Use the root element directly
        if not hasattr(self, 'root') or self.root is None:
            return
            
        # Add LegalMonetaryTotal section
        legal_total = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}LegalMonetaryTotal")
        
        # Line Extension Amount (BT-106) - Sum of Invoice line net amount
        line_total = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}LineExtensionAmount")
        line_total.text = str(flt(self.invoice.net_total, 2))
        line_total.set("currencyID", self.invoice.currency)
        
        # Calculate actual charges (same as E-Invoice core)
        actual_charge_total = sum(tax.tax_amount for tax in self.invoice.taxes if tax.charge_type == "Actual")
        if actual_charge_total:
            # Charge Total Amount (BT-108) - Sum of charges on document level
            charge_total = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}ChargeTotalAmount")
            charge_total.text = str(flt(actual_charge_total, 2))
            charge_total.set("currencyID", self.invoice.currency)
        
        # Tax Exclusive Amount (BT-109) - Invoice total amount without VAT
        tax_exclusive_amount = ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}TaxExclusiveAmount")
        tax_exclusive_amount.text = str(flt(self.invoice.net_total + actual_charge_total, 2))
        tax_exclusive_amount.set("currencyID", self.invoice.currency)
        
        # Tax Amount (BT-110) should be in TaxTotal section, not LegalMonetaryTotal
        
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
    
    # REMOVED: create_peppol_xml - replaced with direct E-Invoice core approach
    
    def initialize_peppol_xml(self) -> ET.Element:
        """Initialize the PEPPOL XML document with root element and namespaces."""
        # Create root element with namespaces
        root = ET.Element('{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice')
        
        # Register namespaces
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
            
        return root
            
    
    
    
    
    def finalize_xml_document(self, root: ET.Element) -> str:
        """Format XML and return as string."""
        # Format XML with proper indentation for readability
        ET.indent(root, space="  ", level=0)
        
        # Convert to string with proper formatting
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
            
    def get_xml_string(self) -> str:
        """Return the XML as a string (for Schematron validation)."""
        if not self.xml_string:
            raise ValueError("No XML generated. Call create_einvoice() first.")
        return self.xml_string
    
    def get_xml_bytes(self, schema: str = None) -> bytes:
        """Return the XML as bytes with optional XSD validation."""
        if not self.xml_string:
            raise ValueError("No XML generated. Call create_einvoice() first.")
        
        if schema:
            return self.serialize_xml(self.xml_string, schema)
        else:
            return self.xml_string.encode('utf-8')
    
    # ============================================================================
    # XML VALIDATION METHODS
    # ============================================================================
    
    def serialize_xml(self, xml_string: str, schema: str = None) -> bytes:
        """
        Serialize XML string to bytes with optional XSD validation.
        
        Args:
            xml_string: XML string to serialize
            schema: XSD schema name (e.g., 'UBL-Invoice-2.1') or None to skip validation
            
        Returns:
            bytes: UTF-8 encoded XML
        """
        xml_bytes = xml_string.encode('utf-8')
        
        # Validate against XSD if schema is provided
        if schema is not None:
            xml_bytes = self.validate_xml_against_xsd(xml_bytes, schema)
        
        return xml_bytes
    
    def validate_xml_against_xsd(self, xml_bytes: bytes, schema: str) -> bytes:
        """
        Validate XML against XSD schema.
        
        Args:
            xml_bytes: XML as bytes
            schema: Schema name (e.g., 'UBL-Invoice-2.1')
            
        Returns:
            bytes: Validated XML
        """
        try:
            from lxml import etree
        except ImportError:
            frappe.logger().warning("Could not validate output as LXML is not installed.")
            return xml_bytes
        
        # Load XSD schema
        xsd_schema = self.load_xsd_schema(schema)
        if xsd_schema is None:
            return xml_bytes
        
        # Parse and validate XML
        return self.parse_and_validate_xml(xml_bytes, xsd_schema)
    
    def load_xsd_schema(self, schema: str):
        """
        Load and compile XSD schema file.
        
        Args:
            schema: Schema name (e.g., 'UBL-Invoice-2.1')
            
        Returns:
            XMLSchema object or None if loading fails
        """
        from lxml import etree
        from pathlib import Path
        
        # XSD schema path
        schema_dir = Path(__file__).parent / "UBL-2.1" / "xsdrt" / "maindoc"
        schema_file = schema_dir / f"{schema}.xsd"
        
        if not schema_file.exists():
            frappe.logger().warning(f"XSD schema not found: {schema_file}. Skipping XSD validation.")
            return None
        
        try:
            schema_doc = etree.parse(str(schema_file))
            return etree.XMLSchema(schema_doc)
        except Exception as e:
            frappe.logger().warning(f"Could not load XSD schema {schema}: {str(e)}")
            return None
    
    def parse_and_validate_xml(self, xml_bytes: bytes, xsd_schema) -> bytes:
        """
        Parse XML with XSD schema validation.
        
        Args:
            xml_bytes: XML as bytes
            xsd_schema: Compiled XSD schema
            
        Returns:
            bytes: Validated and formatted XML
        """
        from lxml import etree
        
        try:
            parser = etree.XMLParser(schema=xsd_schema)
            xml_root = etree.fromstring(xml_bytes, parser)
            
            # Return validated XML with pretty formatting
            return etree.tostring(
                xml_root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
            )
        except etree.XMLSchemaError as e:
            frappe.logger().error(f"XSD validation failed: {str(e)}")
            raise ValueError(f"XSD validation failed: {str(e)}")
        except Exception as e:
            frappe.logger().error(f"XML parsing failed: {str(e)}")
            raise

    # ============================================================================
    # E-INVOICE CORE ALIGNED METHODS
    # ============================================================================
    
    def validate_invoice_fields(self, invoice):
        """Validate required invoice fields."""
        if not getattr(invoice, 'name', None):
            raise ValueError("Invoice name is required")
        if not getattr(invoice, 'company', None):
            raise ValueError("Company is required")
        if not getattr(invoice, 'customer_name', None):
            raise ValueError("Customer name is required")
        if not getattr(invoice, 'posting_date', None):
            raise ValueError("Posting date is required")
        if not getattr(invoice, 'currency', None):
            raise ValueError("Currency is required")
            
    # REMOVED: All old dictionary-based methods replaced with direct E-Invoice core approach



            
            




    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def format_date(self, date):
        """Format date to YYYY-MM-DD string, handling both datetime objects and strings."""
        if not date:
            return None
        
        try:
            # If it's already a string, try to parse and format it
            if isinstance(date, str):
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                # If no format matches, return the original string
                return date
            
            # If it's a datetime object, format it
            if hasattr(date, 'strftime'):
                return date.strftime('%Y-%m-%d')
            
            # If it doesn't have strftime, convert to string
            return str(date)
            
        except Exception as e:
            frappe.logger().error(f"Error formatting date {date} (type: {type(date)}): {str(e)}")
            # Return a safe fallback
            return str(date) if date else None
    
    def calculate_zero_rated_taxable_amount(self, lines: List[Dict[str, Any]], allowances_charges: List[Dict[str, Any]]) -> tuple[float, bool]:
        """Calculate zero-rated taxable amount for BR-Z-08 compliance.

        Returns:
            tuple: (zero_rated_taxable_amount, has_zero_rated_elements)
        """
        # Calculate BR-Z-08: Zero rated taxable amount
        zero_rated_line_total = sum(
            line.get('line_extension_amount', 0)
            for line in lines
            if line.get('tax_category_id') == 'Z'
        )

        zero_rated_allowance_total = sum(
            abs(ac.get('amount', 0))
            for ac in allowances_charges
            if ac.get('charge_indicator') == 'false' and ac.get('tax_category_id') == 'Z'
        )

        zero_rated_charge_total = sum(
            ac.get('amount', 0)
            for ac in allowances_charges
            if ac.get('charge_indicator') == 'true' and ac.get('tax_category_id') == 'Z'
        )

        # BR-Z-08 formula: line totals - allowances + charges
        zero_rated_taxable_amount = zero_rated_line_total - zero_rated_allowance_total + zero_rated_charge_total

        # Check if we have any zero-rated elements (BR-Z-01 requirement)
        has_zero_rated_elements = (
            any(line.get('tax_category_id') == 'Z' for line in lines) or
            any(ac.get('tax_category_id') == 'Z' for ac in allowances_charges)
        )

        return zero_rated_taxable_amount, has_zero_rated_elements

    def extract_tax_info_from_item(self, item) -> tuple[float, str]:
        """Extract VAT rate and category from invoice item.

        Returns:
            tuple: (tax_rate, tax_category_id)
        """
        item_tax_rate = getattr(item, 'item_tax_rate', {})
        if isinstance(item_tax_rate, str):
            try:
                import json
                item_tax_rate = json.loads(item_tax_rate)
            except:
                item_tax_rate = {}

        # Get the VAT rate and category for this line (assume first tax applies)
        tax_rate = 0
        tax_category_id = 'S'  # Default to Standard rated
        for tax_name, rate in item_tax_rate.items():
            if isinstance(rate, (int, float)) and rate > 0:
                tax_rate = rate
                break  # Take the first VAT rate found

        return tax_rate, tax_category_id

    def _get_item_tax_rate(self, item) -> float | None:
        """Get the tax rate for an item from the item tax template and the taxes table.
        
        This is the same logic as the E-Invoice core get_item_rate function.
        
        Args:
            item: SalesInvoiceItem object
            
        Returns:
            float | None: Tax rate percentage, or None if not found
        """
        if item.item_tax_template:
            # Match the accounts from the taxes table with the rate from the item tax template
            tax_template = frappe.get_doc("Item Tax Template", item.item_tax_template)
            applicable_accounts = [tax.account_head for tax in self.invoice.taxes if tax.account_head]

            for item_tax in tax_template.taxes:
                if item_tax.tax_type in applicable_accounts:
                    return item_tax.tax_rate

        # If only one tax is on net total, return its rate
        tax_rates = [invoice_tax.rate for invoice_tax in self.invoice.taxes if invoice_tax.charge_type == "On Net Total"]
        return tax_rates[0] if len(tax_rates) == 1 else None

    def validate_currency_code(self, currency_code):
        """Validate and normalize currency code to ISO 4217 alpha-3 format using code lists."""
        try:
            if not currency_code:
                return 'EUR'  # Default fallback

            # Use CommonCodeRetriever to validate against ISO 4217 code list
            try:
                validated_code = currency_codes.get([("Currency", currency_code)])
                if validated_code:
                    return validated_code
            except Exception as e:
                frappe.logger().warning(f"Error accessing currency codes for '{currency_code}': {str(e)}")

            # If not found in code list, log warning and use default
            frappe.logger().warning(f"Invalid currency code '{currency_code}' not found in ISO 4217 code list, using EUR")
            return 'EUR'

        except Exception as e:
            frappe.logger().error(f"Error validating currency code '{currency_code}': {str(e)}")
            return 'EUR'  # Safe fallback

    def convert_address_to_peppol(self, address) -> dict:
        """Convert Frappe Address to PEPPOL format."""
        try:
            return {
                'street': getattr(address, 'address_line1', ''),
                'additional_street': getattr(address, 'address_line2', ''),
                'city': getattr(address, 'city', ''),
                'postal_code': getattr(address, 'pincode', ''),
                'country_code': getattr(address, 'country', ''),
            }
        except Exception:
            return {
                'street': '',
                'additional_street': '',
                'city': '',
                'postal_code': '',
                'country_code': '',
            }
    
    def convert_contact_to_peppol(self, contact) -> dict:
        """Convert Frappe Contact to PEPPOL format."""
        try:
            first_name = getattr(contact, 'first_name', '')
            last_name = getattr(contact, 'last_name', '')
            name = getattr(contact, 'name', '')
            
            full_name = f"{first_name} {last_name}".strip() if first_name and last_name else name
            
            return {
                'name': full_name,
                'telephone': getattr(contact, 'phone', ''),
                'email': getattr(contact, 'email_id', ''),
            }
        except Exception:
            return {
                'name': '',
                'telephone': '',
                'email': '',
            }
    
    def get_seller_electronic_address(self, company, seller_contact=None) -> dict[str, str] | None:
        """Get seller electronic address using the same logic as main e-invoice application.

        Args:
            company: Company doctype object
            seller_contact: Seller contact object (optional)
            
        Returns:
            dict with 'value' and 'scheme_id' keys, or None if no valid identifier.
        """
        # Priority: Use configured electronic address scheme and address
        if company.electronic_address_scheme and company.electronic_address:
            scheme_id = frappe.db.get_value("Common Code", company.electronic_address_scheme, "common_code")
            if scheme_id:
                return {'value': company.electronic_address, 'scheme_id': scheme_id}

        # Fallback: Use email from contact or company
        electronic_address = None
        if seller_contact and seller_contact.email_id:
            electronic_address = seller_contact.email_id
        else:
            electronic_address = company.email

        if electronic_address:
            return {'value': electronic_address, 'scheme_id': 'EM'}

        return None

    def get_buyer_electronic_address(self, customer, invoice, buyer_contact=None, buyer_address=None) -> dict[str, str] | None:
        """Get buyer electronic address using the same logic as main e-invoice application.

        Args:
            customer: Customer doctype object
            invoice: Sales Invoice doctype object
            buyer_contact: Buyer contact object (optional)
            buyer_address: Buyer address object (optional)
            
        Returns:
            dict with 'value' and 'scheme_id' keys, or None if no valid identifier.
        """
        # Priority: Use configured electronic address scheme and address
        if customer.electronic_address_scheme and customer.electronic_address:
            scheme_id = frappe.db.get_value("Common Code", customer.electronic_address_scheme, "common_code")
            if scheme_id:
                return {'value': customer.electronic_address, 'scheme_id': scheme_id}

        # Fallback: Use email from invoice, contact, or address
        electronic_address = None
        if invoice.contact_email:
            electronic_address = invoice.contact_email
        elif buyer_address and buyer_address.email_id:
            electronic_address = buyer_address.email_id

        if electronic_address:
            return {'value': electronic_address, 'scheme_id': 'EM'}

        return None

    def get_bank_details(self, mode_of_payment: str, company: str) -> tuple[str | None, str | None]:
        """Get the bank details for a mode of payment."""
        try:
            empty_tuple = (None, None)
            if frappe.db.get_value("Mode of Payment", mode_of_payment, "type") != "Bank":
                return empty_tuple

            account = frappe.db.get_value(
                "Mode of Payment Account", {"parent": mode_of_payment, "company": company}, "default_account"
            )
            if not account:
                return empty_tuple

            bank_account_name = frappe.db.get_value(
                "Bank Account", {"account": account, "company": company, "is_company_account": 1, "disabled": 0}
            )
            if not bank_account_name:
                return empty_tuple

            iban, bank = frappe.db.get_value("Bank Account", bank_account_name, ["iban", "bank"])
            if not iban:
                return empty_tuple

            bic = frappe.db.get_value("Bank", bank, "swift_number") if bank else None
            return (iban, bic or None)
            
        except Exception:
            return (None, None)
    
    def get_invoice_type_code(self, invoice) -> str:
        """
        Determine the appropriate PEPPOL invoice type code based on ERPNext document.
        
        Args:
            invoice: ERPNext Sales Invoice document
            
        Returns:
            str: PEPPOL invoice type code
        """
        # Default to commercial invoice
        invoice_type_code = '380'
        
        try:
            # Check if it's a return invoice (Credit note)
            if hasattr(invoice, 'is_return') and invoice.is_return:
                invoice_type_code = '381'  # Credit note
            
            # Check if it's an amended invoice (Corrected invoice)
            elif hasattr(invoice, 'amended_from') and invoice.amended_from:
                invoice_type_code = '384'  # Corrected invoice
            
            # Check if it's a partial invoice (if there's a way to determine this)
            # This could be enhanced based on business logic
            
            # Check if it's a metered services invoice
            # This could be determined by checking if all items are services with specific characteristics
            
            # Check if it's a factored invoice
            # This could be determined by checking if there's a factoring arrangement
            
        except Exception:
            # If any error occurs, default to commercial invoice
            pass
        
        return invoice_type_code
    
    # ============================================================================
    # XML GENERATION METHODS
    # ============================================================================
    
    
    









    def create_tax_total_element(self, root, taxes, currency):
        """Create the main TaxTotal element with total tax amount."""
        tax_total = ET.SubElement(self.root, f"{{{self.namespaces['cac']}}}TaxTotal")
        total_tax_amount = sum(tax.get('amount', 0) for tax in taxes)
        ET.SubElement(tax_total, f"{{{self.namespaces['cbc']}}}TaxAmount", 
                      currencyID=currency).text = str(total_tax_amount)
        return tax_total

    def group_taxes_by_rate_category(self, taxes):
        """Group taxes by rate and category for VAT breakdown."""
        tax_subtotals_map = {}
        for tax in taxes:
            rate = tax.get('rate', 0)
            category_id = tax.get('category_id', 'S')  # Default to 'S' (Standard rated)
            taxable_amount = tax.get('taxable_amount', 0)
            tax_amount = tax.get('amount', 0)

            key = (rate, category_id)
            if key not in tax_subtotals_map:
                tax_subtotals_map[key] = {
                    'taxable_amount': 0,
                    'tax_amount': 0,
                    'percent': rate,
                    'category_id': category_id
                }
            tax_subtotals_map[key]['taxable_amount'] += taxable_amount
            tax_subtotals_map[key]['tax_amount'] += tax_amount
        return tax_subtotals_map

    def create_tax_subtotals(self, tax_total, tax_subtotals_map, currency):
        """Create TaxSubtotal elements for each tax group."""
        for key, subtotal_data in tax_subtotals_map.items():
                tax_subtotal = ET.SubElement(tax_total, f"{{{self.namespaces['cac']}}}TaxSubtotal")
                
            # Taxable Amount (BT-116)
                ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxableAmount", 
                         currencyID=currency).text = str(subtotal_data['taxable_amount'])
                
            # Tax Amount (BT-117)
                ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxAmount", 
                         currencyID=currency).text = str(subtotal_data['tax_amount'])
                
                # Tax Category
                tax_category = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cac']}}}TaxCategory")
                ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID").text = subtotal_data['category_id']

                # VAT Rate (BT-119)
                if subtotal_data['percent'] > 0:
                    ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent").text = str(subtotal_data['percent'])
                
                # Tax Scheme
                tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
                ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
    
        
        
    def calculate_monetary_amounts(self, totals_data, allowances_charges, lines, taxes):
        """Calculate all monetary amounts for legal monetary total."""
        # Line Extension Amount
        line_extension_amount = totals_data.get('line_extension_amount', 0)
        
        # Sum of invoice line net amounts (BT-131)
        line_extension_total = sum(line.get('line_extension_amount', 0) for line in (lines or []))

        # Sum of allowances on document level (BT-107)
        allowance_total = 0.0
        if allowances_charges:
            allowance_total = sum(
                abs(ac.get('amount', 0))
                for ac in allowances_charges
                if ac.get('charge_indicator') == 'false'  # Only allowances
            )

        # Sum of charges on document level (BT-108) - BR-CO-12: Sum of all charges
        charge_total = 0.0
        zero_rated_charge_total = 0.0
        if allowances_charges:
            for ac in allowances_charges:
                if ac.get('charge_indicator') == 'true':  # Only charges
                    amount = ac.get('amount', 0)
                    charge_total += amount  # Include all charges in BT-108
                    # Also track zero-rated charges separately for zero-rated breakdown
                    if ac.get('tax_category_id') == 'Z' or ac.get('tax_category', {}).get('id') == 'Z':
                        zero_rated_charge_total += amount

        # BR-CO-13 formula: Σ(BT-131) - BT-107 + BT-108 (ALL charges)
        tax_exclusive_amount = line_extension_total - allowance_total + charge_total

        # Tax Inclusive Amount (BT-112) - BR-CO-15: BT-109 + BT-110
        total_vat_amount = sum(tax.get('amount', 0) for tax in (taxes or []))
        tax_inclusive_amount = tax_exclusive_amount + total_vat_amount

        # Payable Amount (BT-115) - BR-CO-16: BT-112 - BT-113 + BT-114
        paid_amount = totals_data.get('paid_amount', 0)
        rounding_amount = totals_data.get('rounding_amount', 0)
        payable_amount = tax_inclusive_amount - paid_amount + rounding_amount

        # Round amounts to 2 decimal places to avoid floating point precision errors
        tax_exclusive_amount = round(tax_exclusive_amount, 2)
        tax_inclusive_amount = round(tax_inclusive_amount, 2)
        payable_amount = round(payable_amount, 2)
        charge_total = round(charge_total, 2)
        zero_rated_charge_total = round(zero_rated_charge_total, 2)

        return {
            'line_extension_amount': line_extension_amount,
            'tax_exclusive_amount': tax_exclusive_amount,
            'tax_inclusive_amount': tax_inclusive_amount,
            'payable_amount': payable_amount,
            'allowance_total': allowance_total,
            'charge_total': charge_total,
            'zero_rated_charge_total': zero_rated_charge_total
        }



    def map_unit_code(self, erpnext_unit: str) -> str:
        """Map ERPNext unit codes to PEPPOL standard unit codes using CommonCodeRetriever."""
        if not erpnext_unit:
            return uom_codes.default_code or 'C62'

        # Get unit code from CommonCodeRetriever mapping
        return uom_codes.get([("UOM", erpnext_unit)]) or uom_codes.default_code or 'C62'

    def get_vat_category_code(self, invoice, item=None, tax=None) -> str:
        """Get VAT category code using the same CommonCodeRetriever approach as EInvoiceGenerator."""
        lookup_records = []

        # Try different combinations based on available data (same as EInvoiceGenerator)
        if item:
            # For item-level VAT category (BT-151)
            lookup_records.extend([
                ("Item Tax Template", getattr(item, 'item_tax_template', None)),
                ("Account", getattr(item, 'income_account', None)),
            ])

        if tax:
            # For tax-level VAT category (BT-118)
            lookup_records.extend([
                ("Account", getattr(tax, 'account_head', None)),
            ])

        # Always include invoice-level settings
        lookup_records.extend([
            ("Tax Category", getattr(invoice, 'tax_category', None)),
            ("Sales Taxes and Charges Template", getattr(invoice, 'taxes_and_charges', None)),
        ])

        # Filter out None values
        lookup_records = [(doctype, name) for doctype, name in lookup_records if name]

        # Get the VAT category code using CommonCodeRetriever (same as EInvoiceGenerator)
        category_code = duty_tax_fee_category_codes.get(lookup_records)

        # Return the category code (CommonCodeRetriever handles defaults)
        return category_code 