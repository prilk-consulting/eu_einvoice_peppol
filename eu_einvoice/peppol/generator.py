"""
PEPPOL Generator

This module provides UBL 2.1 XML generation for PEPPOL BIS Billing 3.0
compliant invoices from ERPNext data.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import frappe

from .profiles import PEPPOLProfile, get_profile_info
from .utils import ValidationResult, ValidationMessage, ValidationSeverity


class PEPPOLGenerator:
    """Generates PEPPOL BIS Billing 3.0 compliant UBL 2.1 XML documents."""
    
    def __init__(self, profile: PEPPOLProfile = PEPPOLProfile.PEPPOL_BIS_30):
        self.profile = profile
        self.profile_info = get_profile_info(profile)
        
        # UBL namespaces
        self.namespaces = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        }
    
    def generate_invoice(self, invoice_data: Dict[str, Any]) -> str:
        """Generate UBL 2.1 Invoice XML from ERPNext data."""
        
        try:
            # Debug logging for invoice data
            frappe.logger().info(f"PEPPOL Debug - Invoice data keys: {list(invoice_data.keys())}")
            frappe.logger().info(f"PEPPOL Debug - Lines count: {len(invoice_data.get('lines', []))}")
            frappe.logger().info(f"PEPPOL Debug - Taxes count: {len(invoice_data.get('taxes', []))}")
            
            # Create root element
            root = ET.Element('{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice')
            
            # Register namespaces
            ET.register_namespace('ubl', 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2')
            ET.register_namespace('cbc', 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2')
            ET.register_namespace('cac', 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2')
            
            # Add document header
            self._add_document_header(root, invoice_data)
            
            # Add supplier party
            self._add_supplier_party(root, invoice_data.get('supplier', {}))
            
            # Add customer party
            self._add_customer_party(root, invoice_data.get('customer', {}))
            
            # Add delivery information
            if 'delivery' in invoice_data:
                self._add_delivery(root, invoice_data['delivery'])
            
            # Add payment means
            self._add_payment_means(root, invoice_data.get('payment', {}))
            
            # Add payment terms
            if 'payment_terms' in invoice_data:
                self._add_payment_terms(root, invoice_data['payment_terms'])
            
            # Add tax totals
            self._add_tax_totals(root, invoice_data.get('taxes', []))
            
            # Add legal monetary total
            self._add_legal_monetary_total(root, invoice_data.get('totals', {}))
            
            # Add invoice lines
            lines = invoice_data.get('lines', [])
            frappe.logger().info(f"PEPPOL Debug - Processing {len(lines)} invoice lines")
            frappe.logger().info(f"PEPPOL Debug - Lines data: {lines} (type: {type(lines)})")
            try:
                for i, line in enumerate(lines):
                    frappe.logger().info(f"PEPPOL Debug - Processing line {i+1}: {line}")
                    self._add_invoice_line(root, line)
            except Exception as e:
                frappe.logger().error(f"Error iterating over lines in generate_invoice: {str(e)}")
                frappe.logger().error(f"Lines value: {lines}")
                raise
            
            # Convert to string with proper formatting
            return ET.tostring(root, encoding='unicode', xml_declaration=True)
            
        except Exception as e:
            import traceback
            frappe.logger().error(f"PEPPOL XML generation failed: {str(e)}")
            frappe.logger().error(f"PEPPOL XML generation error traceback: {traceback.format_exc()}")
            raise
    
    def generate_from_erpnext_invoice(self, invoice) -> str:
        """Generate PEPPOL XML directly from ERPNext Sales Invoice document."""
        
        try:
            # Convert ERPNext invoice to PEPPOL format
            frappe.logger().info(f"PEPPOL: Starting conversion for invoice {invoice.name}")
            invoice_data = self._convert_erpnext_to_peppol(invoice)
            frappe.logger().info(f"PEPPOL: Conversion completed for invoice {invoice.name}")
            
            # Generate XML
            frappe.logger().info(f"PEPPOL: Starting XML generation for invoice {invoice.name}")
            xml_string = self.generate_invoice(invoice_data)
            frappe.logger().info(f"PEPPOL: XML generation completed for invoice {invoice.name}")
            
            # Log successful generation
            frappe.logger().info(f"PEPPOL XML generated successfully for invoice {invoice.name}")
            
            return xml_string
            
        except Exception as e:
            import traceback
            frappe.logger().error(f"PEPPOL generation failed for invoice {invoice.name}: {str(e)}")
            frappe.logger().error(f"PEPPOL error traceback: {traceback.format_exc()}")
            raise Exception(f"PEPPOL generation failed: {str(e)}")
    
    def _convert_erpnext_to_peppol(self, invoice) -> Dict[str, Any]:
        """Convert ERPNext Sales Invoice to PEPPOL format."""
        
        try:
            # Debug logging for invoice structure
            frappe.logger().info(f"PEPPOL Debug - Invoice type: {type(invoice)}")
            frappe.logger().info(f"PEPPOL Debug - Invoice name: {getattr(invoice, 'name', 'N/A')}")
            frappe.logger().info(f"PEPPOL Debug - Invoice company: {getattr(invoice, 'company', 'N/A')}")
            frappe.logger().info(f"PEPPOL Debug - Invoice customer_name: {getattr(invoice, 'customer_name', 'N/A')}")
            
            # Debug items and taxes specifically
            items_attr = getattr(invoice, 'items', None)
            taxes_attr = getattr(invoice, 'taxes', None)
            frappe.logger().info(f"PEPPOL Debug - Items attribute: {items_attr} (type: {type(items_attr)})")
            frappe.logger().info(f"PEPPOL Debug - Taxes attribute: {taxes_attr} (type: {type(taxes_attr)})")
            
            # Validate required fields
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
            
            # Get addresses
            seller_address = None
            company_address = getattr(invoice, 'company_address', None)
            if company_address:
                seller_address = frappe.get_doc("Address", company_address)
            
            buyer_address = None
            customer_address = getattr(invoice, 'customer_address', None)
            if customer_address:
                buyer_address = frappe.get_doc("Address", customer_address)
            
            # Get contacts
            seller_contact = None
            company_contact_person = getattr(invoice, 'company_contact_person', None)
            if company_contact_person:
                seller_contact = frappe.get_doc("Contact", company_contact_person)
            
            buyer_contact = None
            contact_person = getattr(invoice, 'contact_person', None)
            if contact_person:
                buyer_contact = frappe.get_doc("Contact", contact_person)
            
            # Get company
            company = frappe.get_doc("Company", invoice.company)
            
            # Debug logging for date fields
            posting_date = getattr(invoice, 'posting_date', None)
            due_date = getattr(invoice, 'due_date', None)
            frappe.logger().info(f"PEPPOL Debug - posting_date: {posting_date} (type: {type(posting_date)})")
            frappe.logger().info(f"PEPPOL Debug - due_date: {due_date} (type: {type(due_date)})")
            
            # Convert to PEPPOL format
            invoice_data = {
                'invoice_id': invoice.name,
                'issue_date': self._format_date(posting_date),
                'due_date': self._format_date(due_date),
                'currency': invoice.currency,
                'buyer_reference': getattr(invoice, 'buyer_reference', ''),
                'supplier': {
                    'name': invoice.company,
                    'tax_id': getattr(invoice, 'company_tax_id', ''),
                    'legal_name': getattr(company, 'company_name', invoice.company),
                    'address': self._convert_address_to_peppol(seller_address) if seller_address else None,
                    'contact': self._convert_contact_to_peppol(seller_contact) if seller_contact else None,
                },
                'customer': {
                    'name': invoice.customer_name,
                    'tax_id': getattr(invoice, 'tax_id', ''),
                    'address': self._convert_address_to_peppol(buyer_address) if buyer_address else None,
                    'contact': self._convert_contact_to_peppol(buyer_contact) if buyer_contact else None,
                },
                'lines': [],
                'taxes': [],
                'totals': {
                    'line_extension_amount': getattr(invoice, 'total', 0),
                    'tax_exclusive_amount': getattr(invoice, 'net_total', 0),
                    'tax_inclusive_amount': getattr(invoice, 'grand_total', 0),
                    'payable_amount': getattr(invoice, 'grand_total', 0),
                }
            }
            
            # Add invoice lines
            items = getattr(invoice, 'items', []) or []
            frappe.logger().info(f"PEPPOL Debug - About to iterate over items: {items} (type: {type(items)})")
            try:
                for item in items:
                    frappe.logger().info(f"PEPPOL Debug - Processing item: {item}")
                    try:
                        line_data = {
                            'id': getattr(item, 'idx', 1),
                            'name': getattr(item, 'item_name', ''),
                            'description': getattr(item, 'description', ''),
                            'quantity': getattr(item, 'qty', 0),
                            'unit_code': self._map_unit_code(getattr(item, 'uom', '')),
                            'unit_price': getattr(item, 'rate', 0),
                            'line_extension_amount': getattr(item, 'amount', 0),
                        }
                        invoice_data['lines'].append(line_data)
                    except Exception as e:
                        frappe.logger().error(f"Error processing invoice line: {str(e)}")
                        continue
            except Exception as e:
                frappe.logger().error(f"Error iterating over items: {str(e)}")
                frappe.logger().error(f"Items value: {items}")
                raise
            
            # Add taxes
            taxes = getattr(invoice, 'taxes', []) or []
            frappe.logger().info(f"PEPPOL Debug - About to iterate over taxes: {taxes} (type: {type(taxes)})")
            try:
                for tax in taxes:
                    frappe.logger().info(f"PEPPOL Debug - Processing tax: {tax}")
                    try:
                        tax_data = {
                            'category_code': 'S',  # Standard rate
                            'rate': getattr(tax, 'rate', 0),
                            'amount': getattr(tax, 'tax_amount', 0),
                            'taxable_amount': getattr(tax, 'total', 0),
                        }
                        invoice_data['taxes'].append(tax_data)
                    except Exception as e:
                        frappe.logger().error(f"Error processing tax: {str(e)}")
                        continue
            except Exception as e:
                frappe.logger().error(f"Error iterating over taxes: {str(e)}")
                frappe.logger().error(f"Taxes value: {taxes}")
                raise
            
            # Add payment information
            mode_of_payment = getattr(invoice, 'mode_of_payment', None)
            if mode_of_payment:
                iban, bic = self._get_bank_details(mode_of_payment, invoice.company)
                if iban:
                    invoice_data['payment'] = {
                        'payment_means_code': '30',  # Credit transfer
                        'account': {
                            'iban': iban,
                            'bic': bic,
                            'name': getattr(company, 'company_name', invoice.company),
                        }
                    }
            
            return invoice_data
            
        except Exception as e:
            import traceback
            frappe.logger().error(f"PEPPOL conversion failed for invoice {invoice.name}: {str(e)}")
            frappe.logger().error(f"PEPPOL conversion error traceback: {traceback.format_exc()}")
            raise
    
    def _format_date(self, date):
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
                frappe.logger().warning(f"Could not parse date string: {date}, using as-is")
                return date
            
            # If it's a datetime object, format it
            if hasattr(date, 'strftime'):
                return date.strftime('%Y-%m-%d')
            
            # If it doesn't have strftime, convert to string
            frappe.logger().warning(f"Date object has no strftime method: {type(date)}, converting to string")
            return str(date)
            
        except Exception as e:
            frappe.logger().error(f"Error formatting date {date} (type: {type(date)}): {str(e)}")
            # Return a safe fallback
            return str(date) if date else None
    
    def _convert_address_to_peppol(self, address) -> dict:
        """Convert Frappe Address to PEPPOL format."""
        try:
            return {
                'street': getattr(address, 'address_line1', ''),
                'additional_street': getattr(address, 'address_line2', ''),
                'city': getattr(address, 'city', ''),
                'postal_code': getattr(address, 'pincode', ''),
                'country_code': getattr(address, 'country', ''),
            }
        except Exception as e:
            frappe.logger().error(f"Error converting address to PEPPOL format: {str(e)}")
            return {
                'street': '',
                'additional_street': '',
                'city': '',
                'postal_code': '',
                'country_code': '',
            }
    
    def _convert_contact_to_peppol(self, contact) -> dict:
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
        except Exception as e:
            frappe.logger().error(f"Error converting contact to PEPPOL format: {str(e)}")
            return {
                'name': '',
                'telephone': '',
                'email': '',
            }
    
    def _get_bank_details(self, mode_of_payment: str, company: str) -> tuple[str | None, str | None]:
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
            
        except Exception as e:
            frappe.logger().error(f"Error getting bank details: {str(e)}")
            return (None, None)
    
    def _add_document_header(self, root: ET.Element, data: Dict[str, Any]):
        """Add document header information."""
        
        try:
            # Customization ID
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}CustomizationID").text = \
                self.profile_info.customization_id
            
            # Profile ID
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}ProfileID").text = \
                self.profile.value
            
            # Document ID
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}ID").text = \
                data.get('invoice_id', 'INV-001')
            
            # Issue Date
            issue_date = data.get('issue_date')
            if not issue_date:
                issue_date = datetime.now().strftime('%Y-%m-%d')
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}IssueDate").text = str(issue_date)
            
            # Due Date
            if 'due_date' in data and data['due_date']:
                ET.SubElement(root, f"{{{self.namespaces['cbc']}}}DueDate").text = str(data['due_date'])
            
            # Invoice Type Code (380 = Commercial Invoice)
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}InvoiceTypeCode").text = '380'
            
            # Document Currency Code
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}DocumentCurrencyCode").text = \
                data.get('currency', 'EUR')
            
            # UBL Version ID
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}UBLVersionID").text = '2.1'
            
            # Buyer Reference
            if 'buyer_reference' in data:
                ET.SubElement(root, f"{{{self.namespaces['cbc']}}}BuyerReference").text = \
                    data['buyer_reference']
                    
        except Exception as e:
            import traceback
            frappe.logger().error(f"PEPPOL document header error: {str(e)}")
            frappe.logger().error(f"PEPPOL document header error traceback: {traceback.format_exc()}")
            raise
    
    def _add_supplier_party(self, root: ET.Element, supplier_data: Dict[str, Any]):
        """Add supplier party information."""
        
        supplier_party = ET.SubElement(root, f"{{{self.namespaces['cac']}}}AccountingSupplierParty")
        party = ET.SubElement(supplier_party, f"{{{self.namespaces['cac']}}}Party")
        
        # Party Identification
        if 'tax_id' in supplier_data:
            party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
            ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID", 
                         schemeID="VA").text = supplier_data['tax_id']
        
        # Party Name
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name").text = \
            supplier_data.get('name', 'Supplier Name')
        
        # Postal Address
        if supplier_data.get('address'):
            self._add_postal_address(party, supplier_data['address'])
        
        # Party Tax Scheme
        if 'tax_id' in supplier_data:
            party_tax = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            ET.SubElement(party_tax, f"{{{self.namespaces['cbc']}}}CompanyID").text = \
                supplier_data['tax_id']
            tax_scheme = ET.SubElement(party_tax, f"{{{self.namespaces['cac']}}}TaxScheme")
            ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
        
        # Party Legal Entity
        if 'legal_name' in supplier_data:
            legal_entity = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyLegalEntity")
            ET.SubElement(legal_entity, f"{{{self.namespaces['cbc']}}}RegistrationName").text = \
                supplier_data['legal_name']
        
        # Contact
        if supplier_data.get('contact'):
            self._add_contact(party, supplier_data['contact'])
    
    def _add_customer_party(self, root: ET.Element, customer_data: Dict[str, Any]):
        """Add customer party information."""
        
        customer_party = ET.SubElement(root, f"{{{self.namespaces['cac']}}}AccountingCustomerParty")
        party = ET.SubElement(customer_party, f"{{{self.namespaces['cac']}}}Party")
        
        # Party Identification
        if 'tax_id' in customer_data:
            party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
            ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID", 
                         schemeID="VA").text = customer_data['tax_id']
        
        # Party Name
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name").text = \
            customer_data.get('name', 'Customer Name')
        
        # Postal Address
        if customer_data.get('address'):
            self._add_postal_address(party, customer_data['address'])
        
        # Party Tax Scheme
        if 'tax_id' in customer_data:
            party_tax = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            ET.SubElement(party_tax, f"{{{self.namespaces['cbc']}}}CompanyID").text = \
                customer_data['tax_id']
            tax_scheme = ET.SubElement(party_tax, f"{{{self.namespaces['cac']}}}TaxScheme")
            ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
        
        # Contact
        if customer_data.get('contact'):
            self._add_contact(party, customer_data['contact'])
    
    def _add_postal_address(self, party: ET.Element, address_data: Dict[str, Any]):
        """Add postal address to party."""
        
        postal_address = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PostalAddress")
        
        if 'street' in address_data:
            ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}StreetName").text = \
                address_data['street']
        
        if 'additional_street' in address_data:
            ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}AdditionalStreetName").text = \
                address_data['additional_street']
        
        if 'city' in address_data:
            ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}CityName").text = \
                address_data['city']
        
        if 'postal_code' in address_data:
            ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}PostalZone").text = \
                address_data['postal_code']
        
        if 'country' in address_data:
            country = ET.SubElement(postal_address, f"{{{self.namespaces['cac']}}}Country")
            ET.SubElement(country, f"{{{self.namespaces['cbc']}}}IdentificationCode").text = \
                address_data['country']
    
    def _add_contact(self, party: ET.Element, contact_data: Dict[str, Any]):
        """Add contact information to party."""
        
        contact = ET.SubElement(party, f"{{{self.namespaces['cac']}}}Contact")
        
        if 'name' in contact_data:
            ET.SubElement(contact, f"{{{self.namespaces['cbc']}}}Name").text = \
                contact_data['name']
        
        if 'telephone' in contact_data:
            ET.SubElement(contact, f"{{{self.namespaces['cbc']}}}Telephone").text = \
                contact_data['telephone']
        
        if 'email' in contact_data:
            ET.SubElement(contact, f"{{{self.namespaces['cbc']}}}ElectronicMail").text = \
                contact_data['email']
    
    def _add_delivery(self, root: ET.Element, delivery_data: Dict[str, Any]):
        """Add delivery information."""
        
        delivery = ET.SubElement(root, f"{{{self.namespaces['cac']}}}Delivery")
        
        if 'delivery_date' in delivery_data:
            ET.SubElement(delivery, f"{{{self.namespaces['cbc']}}}ActualDeliveryDate").text = \
                delivery_data['delivery_date']
        
        if 'address' in delivery_data:
            delivery_location = ET.SubElement(delivery, f"{{{self.namespaces['cac']}}}DeliveryLocation")
            self._add_postal_address(delivery_location, delivery_data['address'])
    
    def _add_payment_means(self, root: ET.Element, payment_data: Dict[str, Any]):
        """Add payment means information."""
        
        payment_means = ET.SubElement(root, f"{{{self.namespaces['cac']}}}PaymentMeans")
        
        # Payment Means Code (1 = Credit Transfer)
        ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentMeansCode").text = \
            payment_data.get('payment_means_code', '1')
        
        # Payment Due Date
        if 'due_date' in payment_data:
            ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentDueDate").text = \
                payment_data['due_date']
        
        # Payment Channel Code
        if 'channel_code' in payment_data:
            ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentChannelCode").text = \
                payment_data['channel_code']
        
        # Payment ID
        if 'payment_id' in payment_data:
            ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentID").text = \
                payment_data['payment_id']
        
        # Payee Financial Account
        if 'account' in payment_data:
            payee_account = ET.SubElement(payment_means, f"{{{self.namespaces['cac']}}}PayeeFinancialAccount")
            ET.SubElement(payee_account, f"{{{self.namespaces['cbc']}}}ID").text = \
                payment_data['account']
    
    def _add_payment_terms(self, root: ET.Element, terms_data: Dict[str, Any]):
        """Add payment terms information."""
        
        payment_terms = ET.SubElement(root, f"{{{self.namespaces['cac']}}}PaymentTerms")
        
        if 'note' in terms_data:
            ET.SubElement(payment_terms, f"{{{self.namespaces['cbc']}}}Note").text = \
                terms_data['note']
        
        if 'amount' in terms_data:
            ET.SubElement(payment_terms, f"{{{self.namespaces['cbc']}}}Amount").text = \
                str(terms_data['amount'])
    
    def _add_tax_totals(self, root: ET.Element, taxes: List[Dict[str, Any]]):
        """Add tax totals information."""
        
        frappe.logger().info(f"PEPPOL Debug - _add_tax_totals called with taxes: {taxes} (type: {type(taxes)})")
        
        # Ensure taxes is a list
        if not taxes:
            taxes = []
        
        frappe.logger().info(f"PEPPOL Debug - About to iterate over {len(taxes)} taxes")
        for i, tax in enumerate(taxes):
            frappe.logger().info(f"PEPPOL Debug - Processing tax {i+1}: {tax}")
            try:
                tax_total = ET.SubElement(root, f"{{{self.namespaces['cac']}}}TaxTotal")
                
                # Tax Amount
                ET.SubElement(tax_total, f"{{{self.namespaces['cbc']}}}TaxAmount", 
                             currencyID=tax.get('currency', 'EUR')).text = str(tax.get('amount', 0))
                
                # Tax Subtotal
                tax_subtotal = ET.SubElement(tax_total, f"{{{self.namespaces['cac']}}}TaxSubtotal")
                
                # Taxable Amount
                ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxableAmount", 
                             currencyID=tax.get('currency', 'EUR')).text = str(tax.get('taxable_amount', 0))
                
                # Tax Amount
                ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxAmount", 
                             currencyID=tax.get('currency', 'EUR')).text = str(tax.get('amount', 0))
                
                # Tax Category
                tax_category = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cac']}}}TaxCategory")
                ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID").text = \
                    tax.get('category_id', 'S')
                
                # Tax Scheme
                tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
                ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
            except Exception as e:
                frappe.logger().error(f"Error processing tax total: {str(e)}")
                continue
    
    def _add_legal_monetary_total(self, root: ET.Element, totals_data: Dict[str, Any]):
        """Add legal monetary total information."""
        
        legal_total = ET.SubElement(root, f"{{{self.namespaces['cac']}}}LegalMonetaryTotal")
        
        # Line Extension Amount
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}LineExtensionAmount", 
                     currencyID=totals_data.get('currency', 'EUR')).text = \
            str(totals_data.get('line_extension_amount', 0))
        
        # Tax Exclusive Amount
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}TaxExclusiveAmount", 
                     currencyID=totals_data.get('currency', 'EUR')).text = \
            str(totals_data.get('tax_exclusive_amount', 0))
        
        # Tax Inclusive Amount
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}TaxInclusiveAmount", 
                     currencyID=totals_data.get('currency', 'EUR')).text = \
            str(totals_data.get('tax_inclusive_amount', 0))
        
        # Payable Amount
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}PayableAmount", 
                     currencyID=totals_data.get('currency', 'EUR')).text = \
            str(totals_data.get('payable_amount', 0))
    
    def _add_invoice_line(self, root: ET.Element, line_data: Dict[str, Any]):
        """Add invoice line information."""
        
        frappe.logger().info(f"PEPPOL Debug - _add_invoice_line called with line_data: {line_data}")
        
        try:
            invoice_line = ET.SubElement(root, f"{{{self.namespaces['cac']}}}InvoiceLine")
            
            # Line ID
            ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}ID").text = \
                str(line_data.get('id', 1))
            
            # Invoiced Quantity
            ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}InvoicedQuantity", 
                         unitCode=self._map_unit_code(line_data.get('unit_code', ''))).text = \
                str(line_data.get('quantity', 1))
            
            # Line Extension Amount
            ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}LineExtensionAmount", 
                         currencyID=line_data.get('currency', 'EUR')).text = \
                str(line_data.get('line_extension_amount', 0))
            
            # Item
            item = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}Item")
            
            # Item Description
            if 'description' in line_data and line_data['description']:
                ET.SubElement(item, f"{{{self.namespaces['cbc']}}}Description").text = \
                    line_data['description']
            
            # Item Name
            ET.SubElement(item, f"{{{self.namespaces['cbc']}}}Name").text = \
                line_data.get('name', 'Item')
            
            # Item Sellers Item Identification
            if 'sellers_item_id' in line_data and line_data['sellers_item_id']:
                sellers_id = ET.SubElement(item, f"{{{self.namespaces['cac']}}}SellersItemIdentification")
                ET.SubElement(sellers_id, f"{{{self.namespaces['cbc']}}}ID").text = \
                    line_data['sellers_item_id']
            
            # Price
            price = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}Price")
            ET.SubElement(price, f"{{{self.namespaces['cbc']}}}PriceAmount", 
                         currencyID=line_data.get('currency', 'EUR')).text = \
                str(line_data.get('unit_price', 0))
            
            # Line Tax Total
            if 'tax' in line_data and line_data['tax']:
                line_tax_total = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}TaxTotal")
                ET.SubElement(line_tax_total, f"{{{self.namespaces['cbc']}}}TaxAmount", 
                             currencyID=line_data.get('currency', 'EUR')).text = \
                    str(line_data['tax'].get('amount', 0))
                
                tax_category = ET.SubElement(line_tax_total, f"{{{self.namespaces['cac']}}}TaxCategory")
                ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID").text = \
                    line_data['tax'].get('category_id', 'S')
                
                tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
                ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
                
        except Exception as e:
            frappe.logger().error(f"Error processing invoice line: {str(e)}")
            frappe.logger().error(f"Line data: {line_data}")
            raise 

    def _map_unit_code(self, erpnext_unit: str) -> str:
        """Map ERPNext unit codes to PEPPOL standard unit codes."""
        if not erpnext_unit:
            return 'C62'  # Default: piece
        
        # PEPPOL unit code mapping
        unit_mapping = {
            'Nos': 'C62',      # Number of items
            'Pcs': 'C62',      # Pieces
            'Piece': 'C62',    # Piece
            'Unit': 'C62',     # Unit
            'Each': 'C62',     # Each
            'Kg': 'KGM',       # Kilogram
            'kg': 'KGM',       # Kilogram
            'Gm': 'GRM',       # Gram
            'gm': 'GRM',       # Gram
            'Ltr': 'LTR',      # Litre
            'ltr': 'LTR',      # Litre
            'Mtr': 'MTR',      # Metre
            'mtr': 'MTR',      # Metre
            'Cm': 'CMT',       # Centimetre
            'cm': 'CMT',       # Centimetre
            'Mm': 'MMT',       # Millimetre
            'mm': 'MMT',       # Millimetre
            'Hr': 'HUR',       # Hour
            'hr': 'HUR',       # Hour
            'Day': 'DAY',      # Day
            'day': 'DAY',      # Day
            'Month': 'MON',    # Month
            'month': 'MON',    # Month
            'Year': 'ANN',     # Year
            'year': 'ANN',     # Year
            'Box': 'XBX',      # Box
            'box': 'XBX',      # Box
            'Pack': 'XPK',     # Pack
            'pack': 'XPK',     # Pack
            'Set': 'SET',      # Set
            'set': 'SET',      # Set
            'Pair': 'PR',      # Pair
            'pair': 'PR',      # Pair
            'Dozen': 'DZN',    # Dozen
            'dozen': 'DZN',    # Dozen
            'Gross': 'GRO',    # Gross
            'gross': 'GRO',    # Gross
        }
        
        return unit_mapping.get(erpnext_unit, 'C62')  # Default to piece if not found 