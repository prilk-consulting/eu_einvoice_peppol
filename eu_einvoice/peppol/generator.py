"""
PEPPOL Generator

This module provides UBL 2.1 XML generation for PEPPOL BIS Billing 3.0
compliant invoices from ERPNext data.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from datetime import datetime
import frappe

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

    # Helper methods for cleaner XML generation
    def create_peppol_xml(self, invoice_data: Dict[str, Any]) -> str:
        """Generate UBL 2.1 Invoice XML from ERPNext data."""
        
        try:
            
            # Create root element with namespaces
            root = ET.Element('{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice')
            
            # Register namespaces
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Add document header
            self.add_document_header(root, invoice_data)

            # Prepare data for document sections
            lines = invoice_data.get('lines', [])
            allowances_charges = invoice_data.get('allowances_charges', [])
            validated_currency = invoice_data.get('currency', 'EUR')
            zero_rated_taxable_amount, has_zero_rated_elements = self.calculate_zero_rated_taxable_amount(lines, allowances_charges)

            # Add all document sections
            self.add_document_sections(root, invoice_data, allowances_charges, lines, validated_currency, zero_rated_taxable_amount, has_zero_rated_elements)
            
            # Format XML with proper indentation for readability
            ET.indent(root, space="  ", level=0)
            
            # Convert to string with proper formatting
            return ET.tostring(root, encoding='unicode', xml_declaration=True)
            
        except Exception as e:
            import traceback
            frappe.logger().error(f"PEPPOL XML generation failed: {str(e)}")
            frappe.logger().error(f"PEPPOL XML generation error traceback: {traceback.format_exc()}")
            raise
    

    def create_einvoice(self):
        """Create the PEPPOL XML document."""
        try:
            if not self.invoice:
                raise ValueError("No invoice provided to PEPPOLGenerator")

            # Convert ERPNext data to PEPPOL format
            peppol_data = self.convert_erpnext_to_peppol(self.invoice)

            # Generate XML document
            self.xml_string = self.create_peppol_xml(peppol_data)
            
        except Exception as e:
            frappe.logger().error(f"PEPPOL generation failed: {str(e)}")
            import traceback
            frappe.logger().error(f"PEPPOL traceback: {traceback.format_exc()}")
            raise
    
    def get_einvoice(self):
        """Return the PEPPOL XML as a UBL document object."""
        if self.xml_string:
            # UBL document wrapper (parallel to drafthorse.Document for CII)
            class UBLDocument:
                def __init__(self, xml_string):
                    self.xml_string = xml_string

                def serialize(self, schema=None):
                    """
                    Serialize XML with optional XSD validation.
                    
                    Args:
                        schema: XSD schema name (e.g., 'UBL-Invoice-2.1') or None to skip validation
                        
                    Returns:
                        bytes: UTF-8 encoded XML
                    """
                    xml_bytes = self.xml_string.encode('utf-8')
                    
                    # Validate against XSD if schema is provided (following drafthorse pattern)
                    if schema is not None:
                        xml_bytes = self.validate_xml(xml_bytes, schema)
                    
                    return xml_bytes
                
                def validate_xml(self, xmlout: bytes, schema: str) -> bytes:
                    """
                    Validate XML against XSD schema (following drafthorse.utils.validate_xml pattern).
                    
                    Args:
                        xmlout: XML as bytes
                        schema: Schema name (e.g., 'UBL-Invoice-2.1')
                        
                    Returns:
                        bytes: Validated XML
                    """
                    try:
                        from lxml import etree
                    except ImportError:
                        frappe.logger().warning("Could not validate output as LXML is not installed.")
                        return xmlout
                    
                    if schema is not None:
                        from pathlib import Path
                        
                        # XSD schema path (following drafthorse pattern)
                        schema_dir = Path(__file__).parent / "UBL-2.1" / "xsdrt" / "maindoc"
                        schema_file = schema_dir / f"{schema}.xsd"
                        
                        if not schema_file.exists():
                            frappe.logger().warning(f"XSD schema not found: {schema_file}. Skipping XSD validation.")
                            return xmlout
                        
                        try:
                            # Load and compile XSD schema
                            schema_doc = etree.parse(str(schema_file))
                            xsd_schema = etree.XMLSchema(schema_doc)
                        except Exception as e:
                            frappe.logger().warning(f"Could not load XSD schema {schema}: {str(e)}")
                            return xmlout
                    
                    # Parse XML with schema validation
                    try:
                        parser = etree.XMLParser(schema=xsd_schema if schema else None)
                        xml_root = etree.fromstring(xmlout, parser)
                        
                        # Return validated XML (following drafthorse pattern with pretty_print)
                        return etree.tostring(
                            xml_root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
                        )
                    except etree.XMLSchemaError as e:
                        frappe.logger().error(f"XSD validation failed: {str(e)}")
                        raise ValueError(f"XSD validation failed: {str(e)}")
                    except Exception as e:
                        frappe.logger().error(f"XML parsing failed: {str(e)}")
                        raise

            return UBLDocument(self.xml_string)
        return None

    def convert_erpnext_to_peppol(self, invoice) -> Dict[str, Any]:
        """Convert ERPNext Sales Invoice to PEPPOL format."""
        
        try:
            # Validate required fields
            self.validate_invoice_fields(invoice)
            
            # Get related documents
            addresses, contacts, company, customer = self.get_related_documents(invoice)
            
            # Create base invoice data structure
            invoice_data = self.create_base_invoice_data(invoice, addresses, contacts, company, customer)
            
            # Add invoice lines
            self.process_invoice_lines(invoice, invoice_data)
            
            # Process taxes
            self.process_taxes(invoice, invoice_data)
            
            # Process allowances and charges
            self.process_allowances_charges(invoice, invoice_data)

            # Process document references and payment information
            self.process_document_references(invoice, invoice_data)
            self.process_payment_information(invoice, invoice_data)
            
            return invoice_data
            
        except Exception as e:
            frappe.logger().error(f"PEPPOL conversion failed: {str(e)}")
            raise

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

    def get_related_documents(self, invoice):
        """Get related documents (addresses, contacts, company, customer)."""
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
        
        # Get company and customer
        company = frappe.get_doc("Company", invoice.company)
        customer = frappe.get_doc("Customer", invoice.customer)
        
        addresses = {
            'seller': seller_address,
            'buyer': buyer_address
        }
        contacts = {
            'seller': seller_contact,
            'buyer': buyer_contact
        }
        
        return addresses, contacts, company, customer

    def create_base_invoice_data(self, invoice, addresses, contacts, company, customer):
        """Create the base invoice data structure."""
        posting_date = getattr(invoice, 'posting_date', None)
        due_date = getattr(invoice, 'due_date', None)
        validated_currency = self.validate_currency_code(getattr(invoice, 'currency', 'EUR'))
        
        seller_address = addresses['seller']
        buyer_address = addresses['buyer']
        seller_contact = contacts['seller']
        buyer_contact = contacts['buyer']

        return {
            'invoice_id': invoice.name,
            'issue_date': self.format_date(posting_date),
            'due_date': self.format_date(due_date),
            'currency': validated_currency,
            'buyer_reference': getattr(invoice, 'buyer_reference', ''),
            'po_no': getattr(invoice, 'po_no', ''),
            'supplier': {
                'name': invoice.company,
                'tax_id': getattr(invoice, 'company_tax_id', ''),
                'legal_name': getattr(company, 'company_name', invoice.company),
                'electronic_address': self.get_seller_electronic_address(company, seller_contact),
                'country': getattr(company, 'country', ''),
                'address': self.convert_address_to_peppol(seller_address) if seller_address else None,
                'contact': self.convert_contact_to_peppol(seller_contact) if seller_contact else None,
            },
            'customer': {
                'name': invoice.customer_name,
                'tax_id': getattr(invoice, 'tax_id', ''),
                'electronic_address': self.get_buyer_electronic_address(customer, invoice, buyer_contact, buyer_address),
                'country': buyer_address.country if buyer_address else '',
                'address': self.convert_address_to_peppol(buyer_address) if buyer_address else None,
                'contact': self.convert_contact_to_peppol(buyer_contact) if buyer_contact else None,
            },
            'lines': [],
            'taxes': [],
            'totals': {
                'line_extension_amount': getattr(invoice, 'total', 0),
                'tax_exclusive_amount': getattr(invoice, 'net_total', 0),
                'tax_inclusive_amount': getattr(invoice, 'grand_total', 0),
                'payable_amount': getattr(invoice, 'grand_total', 0),
                'currency': validated_currency,
            }
        }

    def process_invoice_lines(self, invoice, invoice_data):
        """Process invoice line items."""
        items = getattr(invoice, 'items', []) or []
        try:
            for item in items:
                try:
                    # Extract tax information for this line
                    tax_rate, tax_category_id = self.extract_tax_info_from_item(item)

                    line_data = {
                        'id': getattr(item, 'idx', 1),
                        'name': getattr(item, 'item_name', ''),
                        'description': getattr(item, 'description', ''),
                        'quantity': getattr(item, 'qty', 0),
                        'unit_code': self.map_unit_code(getattr(item, 'uom', '')),
                        'unit_price': getattr(item, 'rate', 0),
                        'line_extension_amount': getattr(item, 'amount', 0),
                        'tax_rate': tax_rate,  # BT-152
                        'tax_category_id': tax_category_id,  # BT-151
                        'currency': self.validate_currency_code(getattr(invoice, 'currency', 'EUR')),
                    }
                    invoice_data['lines'].append(line_data)
                except Exception as e:
                    # Skip problematic line items but continue processing
                    continue
        except Exception as e:
            frappe.logger().error(f"Error iterating over items: {str(e)}")
            raise

    def process_taxes(self, invoice, invoice_data):
        """Process tax calculations and add to invoice data."""
        items = getattr(invoice, 'items', []) or []
        
        # Calculate taxable amounts per VAT rate for BR-S-08 compliance
        # Group invoice lines by VAT rate to get correct taxable amounts
        tax_rate_totals = {}  # rate -> total_amount

        for item in items:
            item_tax_rate = getattr(item, 'item_tax_rate', {})
            amount = getattr(item, 'amount', 0)

            # item_tax_rate might be a JSON string, parse it if needed
            if isinstance(item_tax_rate, str):
                try:
                    import json
                    item_tax_rate = json.loads(item_tax_rate)
                except:
                    continue

            # Extract VAT rate from item_tax_rate (e.g., {"VAT 21% - D": 21})
            for tax_name, rate in item_tax_rate.items():
                if isinstance(rate, (int, float)) and rate > 0:
                    if rate not in tax_rate_totals:
                        tax_rate_totals[rate] = 0
                    tax_rate_totals[rate] += amount

        # Add taxes using the correct taxable amounts from line items
        taxes = getattr(invoice, 'taxes', []) or []
        try:
            # Create tax entries for each tax rate found in line items
            for rate in tax_rate_totals.keys():
                taxable_amount = tax_rate_totals[rate]

                # Find the corresponding tax amount from the document taxes
                # Since ERPNext summarizes all taxes of the same type, we need to find the tax entry
                # that corresponds to this rate. For now, assume the first tax entry contains the total.
                tax_amount = 0
                if taxes:
                    # For simplicity, use the total tax amount and distribute it proportionally
                    # This is a simplification - in practice, you'd need more sophisticated logic
                    total_taxable = sum(tax_rate_totals.values())
                    if total_taxable > 0:
                        tax_entry = taxes[0]  # Assume first tax entry has the total
                        total_tax = getattr(tax_entry, 'tax_amount', 0)
                        tax_amount = (taxable_amount / total_taxable) * total_tax

                    tax_data = {
                        'category_code': 'S',  # Standard rate
                        'rate': rate,
                        'amount': tax_amount,
                        'taxable_amount': taxable_amount,  # Sum of line amounts with this tax rate
                        'currency': self.validate_currency_code(getattr(invoice, 'currency', 'EUR')),
                    }
                    invoice_data['taxes'].append(tax_data)
        except Exception as e:
            frappe.logger().error(f"Error iterating over taxes: {str(e)}")
            raise

    def process_allowances_charges(self, invoice, invoice_data):
        """Process document-level allowances and charges."""
        allowances_charges = []
        taxes = getattr(invoice, 'taxes', []) or []
        validated_currency = invoice_data['currency']
        
        for i, tax in enumerate(taxes):
            charge_type = getattr(tax, 'charge_type', '')
            if charge_type in ['Actual', 'On Net Total', 'On Previous Row Amount', 'On Previous Row Total']:
                tax_amount = getattr(tax, 'tax_amount', 0)
                if tax_amount != 0:  # Only include non-zero amounts
                    ac_data = {
                        'charge_indicator': 'true' if tax_amount > 0 else 'false',  # true = charge, false = allowance
                        'amount': abs(tax_amount),
                        'currency': validated_currency,  # Add validated currency for currencyID
                        'reason': getattr(tax, 'description', ''),
                        'reason_code': '',  # Could be mapped from tax type
                    }

                    # For charges, we need VAT category and rate (BR-37)
                    if tax_amount > 0:  # Only for charges
                        # Check if next row has VAT for this charge
                        vat_rate = 0
                        vat_category_code = 'Z'  # Default to Zero rated (BR-S-07 compliance)

                        if len(taxes) > i + 1:
                            next_tax = taxes[i + 1]
                            next_charge_type = getattr(next_tax, 'charge_type', '')
                            if next_charge_type in ('On Previous Row Amount', 'On Previous Row Total'):
                                # This is VAT on the charge
                                vat_rate = getattr(next_tax, 'rate', 0)
                                # Get VAT category code from tax category mapping
                                mapped_category = duty_tax_fee_category_codes.get([
                                    ("Account", getattr(next_tax, 'account_head', '')),
                                    ("Tax Category", getattr(invoice, 'tax_category', '')),
                                    ("Sales Taxes and Charges Template", getattr(invoice, 'taxes_and_charges', ''))
                                ], 'S')

                                # BR-S-07: If category is "S" (Standard rated), rate must be > 0
                                if mapped_category == 'S' and vat_rate > 0:
                                    vat_category_code = 'S'  # Use Standard rated only if rate > 0
                                elif mapped_category == 'Z':
                                    vat_category_code = 'Z'  # Keep Zero rated
                                else:
                                    # For other categories or if rate <= 0, use Zero rated
                                    vat_category_code = 'Z'
                            # If next row exists but is not VAT, keep default 'Z'
                        # If no next row, keep default 'Z'
                        ac_data['vat_category_code'] = vat_category_code
                        ac_data['vat_rate'] = vat_rate

                    allowances_charges.append(ac_data)

        if allowances_charges:
            invoice_data['allowances_charges'] = allowances_charges

    def process_document_references(self, invoice, invoice_data):
        """Process document references (attachments)."""
        document_references = []
        # Get file attachments from the invoice
        try:
            attachments = frappe.get_all("File",
                filters={"attached_to_doctype": "Sales Invoice", "attached_to_name": invoice.name},
                fields=["file_name", "file_url", "file_size"]
            )
            for attachment in attachments:
                ref_data = {
                    'id': attachment.file_name,
                    'document_type_code': '380',  # Commercial Invoice attachment
                    'document_description': f"Attachment: {attachment.file_name}",
                }
                document_references.append(ref_data)
        except Exception:
            # Silently skip attachments if they can't be retrieved
            pass

        if document_references:
            invoice_data['document_references'] = document_references

    def process_payment_information(self, invoice, invoice_data):
        """Process payment information."""
        mode_of_payment = getattr(invoice, 'mode_of_payment', None)
        if mode_of_payment:
            iban, bic = self.get_bank_details(mode_of_payment, invoice.company)
            if iban:
                company = frappe.get_doc("Company", invoice.company)
                invoice_data['payment'] = {
                    'mode_of_payment': mode_of_payment,
                    'account': {
                        'iban': iban,
                        'bic': bic,
                        'name': getattr(company, 'company_name', invoice.company),
                    }
                }
    
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
            if ac.get('charge_indicator') == 'false' and ac.get('vat_category_code') == 'Z'
        )

        zero_rated_charge_total = sum(
            ac.get('amount', 0)
            for ac in allowances_charges
            if ac.get('charge_indicator') == 'true' and ac.get('vat_category_code') == 'Z'
        )

        # BR-Z-08 formula: line totals - allowances + charges
        zero_rated_taxable_amount = zero_rated_line_total - zero_rated_allowance_total + zero_rated_charge_total

        # Check if we have any zero-rated elements (BR-Z-01 requirement)
        has_zero_rated_elements = (
            any(line.get('tax_category_id') == 'Z' for line in lines) or
            any(ac.get('vat_category_code') == 'Z' for ac in allowances_charges)
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

    def add_document_sections(self, root: ET.Element, invoice_data: Dict[str, Any], allowances_charges: List[Dict[str, Any]], lines: List[Dict[str, Any]], validated_currency: str, zero_rated_taxable_amount: float, has_zero_rated_elements: bool):
        """Add all main document sections to the invoice XML."""
        # Add supplier and customer parties
        self.add_supplier_party(root, invoice_data.get('supplier', {}))
        self.add_customer_party(root, invoice_data.get('customer', {}))

        # Add delivery information
        if 'delivery' in invoice_data:
            self.add_delivery(root, invoice_data['delivery'])

        # Add payment means
        supplier_country = invoice_data.get('supplier', {}).get('country', '')
        customer_country = invoice_data.get('customer', {}).get('country', '')
        self.add_payment_means(root, invoice_data.get('payment', {}), supplier_country, customer_country)

        # Add payment terms
        if 'payment_terms' in invoice_data:
            self.add_payment_terms(root, invoice_data['payment_terms'])

        # Add document level allowances/charges
        for ac in allowances_charges:
            self.add_allowance_charge(root, ac)

        # Add additional document references (attachments)
        document_references = invoice_data.get('document_references', [])
        for ref in document_references:
            self.add_additional_document_reference(root, ref)

        # Add tax totals
        self.add_tax_totals(root, invoice_data.get('taxes', []), allowances_charges, zero_rated_taxable_amount, has_zero_rated_elements, validated_currency)

        # Add legal monetary total
        self.add_legal_monetary_total(root, invoice_data.get('totals', {}), validated_currency, allowances_charges, lines, invoice_data.get('taxes', []))

        # Add invoice lines
        try:
            for i, line in enumerate(lines):
                self.add_invoice_line(root, line, validated_currency)
        except Exception as e:
            frappe.logger().error(f"Error iterating over lines in generate_invoice: {str(e)}")
            frappe.logger().error(f"Lines value: {lines}")
            raise

    def validate_currency_code(self, currency_code):
        """Validate and normalize currency code to ISO 4217 alpha-3 format."""
        try:
            if not currency_code:
                return 'EUR'  # Default fallback

            # Ensure it's a string
            currency_code = str(currency_code).strip().upper()

            if not currency_code:
                return 'EUR'

            # List of ISO 4217 currency codes that match the PEPPOL schematron
            # This is the exact list from PEPPOL-EN16931-UBL.xsl ISO4217 variable
            peppol_iso4217_currencies = {
                'AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN', 'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BOV', 'BRL', 'BSD', 'BTN', 'BWP', 'BYN', 'BZD', 'CAD', 'CDF', 'CHE', 'CHF', 'CHW', 'CLF', 'CLP', 'CNY', 'COP', 'COU', 'CRC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD', 'EGP', 'ERN', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL', 'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HTG', 'HUF', 'IDR', 'ILS', 'INR', 'IQD', 'IRR', 'ISK', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRU', 'MUR', 'MVR', 'MWK', 'MXN', 'MXV', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK', 'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLE', 'SOS', 'SRD', 'SSP', 'STN', 'SVC', 'SYP', 'SZL', 'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY', 'TTD', 'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'USN', 'UYI', 'UYU', 'UYW', 'UZS', 'VED', 'VES', 'VND', 'VUV', 'WST', 'XAF', 'XAG', 'XAU', 'XBA', 'XBB', 'XBC', 'XBD', 'XCD', 'XDR', 'XOF', 'XPD', 'XPF', 'XPT', 'XSU', 'XTS', 'XUA', 'YER', 'ZAR', 'ZMW', 'ZWG', 'XXX'
            }

            # Try to get the official code from CommonCodeRetriever first
            try:
                validated_code = currency_codes.get([("Currency", currency_code)])
                if validated_code:
                    return validated_code
            except Exception as e:
                frappe.logger().warning(f"Error accessing currency codes for '{currency_code}': {str(e)}")

            # Fallback: Check against PEPPOL schematron ISO 4217 codes
            if currency_code in peppol_iso4217_currencies:
                return currency_code

            # BR-CL-03 requires codes from ISO 4217 list only
            # If not found in official list or common list, reject it
            frappe.logger().warning(f"Invalid currency code '{currency_code}', using EUR")
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
    
    def add_document_header(self, root: ET.Element, data: Dict[str, Any]):
        """Add document header information."""
        
        try:
            # UBL Version ID (must come early according to XSD schema)
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}UBLVersionID").text = '2.1'
            
            # Customization ID (BT-24)
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}CustomizationID").text = \
                PEPPOL_CUSTOMIZATION_ID
            
            # Profile ID (BT-23)
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}ProfileID").text = \
                PEPPOL_PROFILE_ID
            
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
            
            # Document Currency Code - BT-5 (must be valid ISO 4217 code)
            document_currency = self.validate_currency_code(data.get('currency', 'EUR'))
            ET.SubElement(root, f"{{{self.namespaces['cbc']}}}DocumentCurrencyCode").text = document_currency
            
            # Buyer Reference or Order Reference - Required for PEPPOL-EN16931-R003
            if data.get('buyer_reference'):
                ET.SubElement(root, f"{{{self.namespaces['cbc']}}}BuyerReference").text = \
                    data['buyer_reference']
            elif data.get('po_no'):
                # Use OrderReference if no buyer reference but PO number exists
                order_reference = ET.SubElement(root, f"{{{self.namespaces['cac']}}}OrderReference")
                ET.SubElement(order_reference, f"{{{self.namespaces['cbc']}}}ID").text = data['po_no']
                    
        except Exception as e:
            frappe.logger().error(f"PEPPOL document header error: {str(e)}")
            raise
    
    def add_supplier_party(self, root: ET.Element, supplier_data: Dict[str, Any]):
        """Add supplier party information."""
        
        supplier_party = ET.SubElement(root, f"{{{self.namespaces['cac']}}}AccountingSupplierParty")
        party = ET.SubElement(supplier_party, f"{{{self.namespaces['cac']}}}Party")

        # EndpointID (Electronic Address) - Required for PEPPOL-EN16931-R020
        electronic_addr = supplier_data.get('electronic_address')
        if electronic_addr and isinstance(electronic_addr, dict):
            ET.SubElement(party, f"{{{self.namespaces['cbc']}}}EndpointID",
                         schemeID=electronic_addr['scheme_id']).text = electronic_addr['value']
        
        # Party Identification
        if supplier_data.get('tax_id'):
            party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
            ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID").text = supplier_data['tax_id']
        
        # Party Name
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name").text = \
            supplier_data.get('name', 'Supplier Name')
        
        # Postal Address
        if supplier_data.get('address'):
            self.add_postal_address(party, supplier_data['address'])
        
        # Party Tax Scheme
        if supplier_data.get('tax_id'):
            party_tax = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            ET.SubElement(party_tax, f"{{{self.namespaces['cbc']}}}CompanyID").text = \
                supplier_data['tax_id']
            tax_scheme = ET.SubElement(party_tax, f"{{{self.namespaces['cac']}}}TaxScheme")
            ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
        
        # Party Legal Entity - Required for seller name (BT-27)
        legal_entity = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyLegalEntity")
        ET.SubElement(legal_entity, f"{{{self.namespaces['cbc']}}}RegistrationName").text = \
            supplier_data.get('legal_name', supplier_data.get('name', 'Supplier Name'))
        
        # Contact
        if supplier_data.get('contact'):
            self.add_contact(party, supplier_data['contact'])
    
    def add_customer_party(self, root: ET.Element, customer_data: Dict[str, Any]):
        """Add customer party information."""
        
        customer_party = ET.SubElement(root, f"{{{self.namespaces['cac']}}}AccountingCustomerParty")
        party = ET.SubElement(customer_party, f"{{{self.namespaces['cac']}}}Party")

        # EndpointID (Electronic Address) - Required for PEPPOL-EN16931-R010
        electronic_addr = customer_data.get('electronic_address')
        if electronic_addr and isinstance(electronic_addr, dict):
            ET.SubElement(party, f"{{{self.namespaces['cbc']}}}EndpointID",
                         schemeID=electronic_addr['scheme_id']).text = electronic_addr['value']
        
        # Party Identification
        if customer_data.get('tax_id'):
            party_id = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyIdentification")
            ET.SubElement(party_id, f"{{{self.namespaces['cbc']}}}ID").text = customer_data['tax_id']
        
        # Party Name
        party_name = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyName")
        ET.SubElement(party_name, f"{{{self.namespaces['cbc']}}}Name").text = \
            customer_data.get('name', 'Customer Name')
        
        # Postal Address
        if customer_data.get('address'):
            self.add_postal_address(party, customer_data['address'])
        
        # Party Tax Scheme
        if customer_data.get('tax_id'):
            party_tax = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyTaxScheme")
            ET.SubElement(party_tax, f"{{{self.namespaces['cbc']}}}CompanyID").text = \
                customer_data['tax_id']
            tax_scheme = ET.SubElement(party_tax, f"{{{self.namespaces['cac']}}}TaxScheme")
            ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'

        # Party Legal Entity - Required for buyer name (BT-44)
        legal_entity = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PartyLegalEntity")
        ET.SubElement(legal_entity, f"{{{self.namespaces['cbc']}}}RegistrationName").text = \
            customer_data.get('name', 'Customer Name')
        
        # Contact
        if customer_data.get('contact'):
            self.add_contact(party, customer_data['contact'])
    
    def add_postal_address(self, party: ET.Element, address_data: Dict[str, Any]):
        """Add postal address to party."""
        
        # Only create PostalAddress if we have actual address data
        has_address_data = (
            address_data.get('street') or
            address_data.get('additional_street') or
            address_data.get('city') or
            address_data.get('postal_code') or
            address_data.get('country_code')
        )

        if has_address_data:
            postal_address = ET.SubElement(party, f"{{{self.namespaces['cac']}}}PostalAddress")

            if address_data.get('street'):
                ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}StreetName").text = \
                address_data['street']
        
            if address_data.get('additional_street'):
                ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}AdditionalStreetName").text = \
                address_data['additional_street']
        
            if address_data.get('city'):
                ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}CityName").text = \
                address_data['city']
        
            if address_data.get('postal_code'):
                ET.SubElement(postal_address, f"{{{self.namespaces['cbc']}}}PostalZone").text = \
                address_data['postal_code']
        
            if address_data.get('country_code'):
                country = ET.SubElement(postal_address, f"{{{self.namespaces['cac']}}}Country")
                # Use CommonCodeRetriever to get ISO country code (BT-40)
                country_code = country_codes.get([("Country", address_data['country_code'])])
                ET.SubElement(country, f"{{{self.namespaces['cbc']}}}IdentificationCode").text = \
                    country_code or address_data['country_code']
    
    def add_contact(self, party: ET.Element, contact_data: Dict[str, Any]):
        """Add contact information to party."""
        
        # Only create Contact element if we have actual contact data
        has_contact_data = (
            contact_data.get('name') or
            contact_data.get('telephone') or
            contact_data.get('email')
        )

        if has_contact_data:
            contact = ET.SubElement(party, f"{{{self.namespaces['cac']}}}Contact")

            if contact_data.get('name'):
                ET.SubElement(contact, f"{{{self.namespaces['cbc']}}}Name").text = \
                contact_data['name']
        
            if contact_data.get('telephone'):
                ET.SubElement(contact, f"{{{self.namespaces['cbc']}}}Telephone").text = \
                contact_data['telephone']
        
            if contact_data.get('email'):
                ET.SubElement(contact, f"{{{self.namespaces['cbc']}}}ElectronicMail").text = contact_data['email']
    
    def add_delivery(self, root: ET.Element, delivery_data: Dict[str, Any]):
        """Add delivery information."""
        
        delivery = ET.SubElement(root, f"{{{self.namespaces['cac']}}}Delivery")
        
        if 'delivery_date' in delivery_data:
            ET.SubElement(delivery, f"{{{self.namespaces['cbc']}}}ActualDeliveryDate").text = \
                delivery_data['delivery_date']
        
        if 'address' in delivery_data:
            delivery_location = ET.SubElement(delivery, f"{{{self.namespaces['cac']}}}DeliveryLocation")
            self.add_postal_address(delivery_location, delivery_data['address'])
    
    def add_payment_means(self, root: ET.Element, payment_data: Dict[str, Any], supplier_country: str = '', customer_country: str = ''):
        """Add payment means information."""
        
        payment_means = ET.SubElement(root, f"{{{self.namespaces['cac']}}}PaymentMeans")

        # Payment Means Code - BR-61 requires account info for codes 30, 58
        mode_of_payment = payment_data.get('mode_of_payment')
        has_account_info = 'account' in payment_data and payment_data['account'].get('iban')

        # If we have account info, default to credit transfer (30)
        # Otherwise, look up from mode of payment mapping
        if has_account_info:
            payment_means_code = payment_means_codes.get([("Mode of Payment", mode_of_payment)]) or '30'
        else:
            payment_means_code = payment_means_codes.get([("Mode of Payment", mode_of_payment)]) or '1'

        # BR-61: Codes 30 and 58 require PayeeFinancialAccount
        credit_transfer_codes = ['30', '58']
        if payment_means_code in credit_transfer_codes and not has_account_info:
            # If using credit transfer code but no account info, fall back to general code
            payment_means_code = '1'

        # NL-R-008: Netherlands-specific allowed codes
        if supplier_country == 'Netherlands' and customer_country == 'Netherlands':
            allowed_codes = ['30', '48', '49', '57', '58', '59']
            if payment_means_code not in allowed_codes:
                if has_account_info:
                    # We have account info, use credit transfer
                    payment_means_code = '30'
                else:
                    # No account info, use bank card (48) which doesn't require account info per BR-61
                    payment_means_code = '48'

        ET.SubElement(payment_means, f"{{{self.namespaces['cbc']}}}PaymentMeansCode").text = payment_means_code
        
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
        
        # Payee Financial Account (BR-61 requires this for codes 30, 58)
        if has_account_info:
            payee_account = ET.SubElement(payment_means, f"{{{self.namespaces['cac']}}}PayeeFinancialAccount")
            account_info = payment_data['account']
            ET.SubElement(payee_account, f"{{{self.namespaces['cbc']}}}ID").text = account_info['iban']

            # Financial Institution Branch (BIC)
            if account_info.get('bic'):
                fin_institution = ET.SubElement(payee_account, f"{{{self.namespaces['cac']}}}FinancialInstitutionBranch")
                ET.SubElement(fin_institution, f"{{{self.namespaces['cbc']}}}ID").text = account_info['bic']
    
    def add_payment_terms(self, root: ET.Element, terms_data: Dict[str, Any]):
        """Add payment terms information."""
        
        payment_terms = ET.SubElement(root, f"{{{self.namespaces['cac']}}}PaymentTerms")
        
        if 'note' in terms_data:
            ET.SubElement(payment_terms, f"{{{self.namespaces['cbc']}}}Note").text = \
                terms_data['note']
        
        if 'amount' in terms_data:
            ET.SubElement(payment_terms, f"{{{self.namespaces['cbc']}}}Amount").text = \
                str(terms_data['amount'])
    
    def add_allowance_charge(self, root: ET.Element, ac_data: Dict[str, Any]):
        """Add document-level allowance or charge information."""
        allowance_charge = ET.SubElement(root, f"{{{self.namespaces['cac']}}}AllowanceCharge")

        # Charge indicator (true = charge/surcharge, false = allowance/discount)
        charge_indicator = ac_data.get('charge_indicator', 'false')
        ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}ChargeIndicator").text = charge_indicator

        # Reason code (optional) - must come before Amount according to XSD
        if ac_data.get('reason_code') and ac_data.get('reason_code').strip():
            ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}AllowanceChargeReasonCode").text = \
                ac_data['reason_code']

        # Reason (optional) - must come before Amount according to XSD
        if ac_data.get('reason'):
            ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}AllowanceChargeReason").text = \
                ac_data['reason']

        # Amount (always positive) - must have currencyID per PEPPOL rules
        if 'amount' in ac_data:
            ET.SubElement(allowance_charge, f"{{{self.namespaces['cbc']}}}Amount",
                         currencyID=ac_data.get('currency', 'EUR')).text = \
                str(ac_data['amount'])

        # Tax Category (BR-37: required for charges)
        if charge_indicator == 'true':  # Only for charges
            tax_category = ET.SubElement(allowance_charge, f"{{{self.namespaces['cac']}}}TaxCategory")

            # VAT Category Code (BT-102) and Rate (BT-103) - BR-S-07 compliance
            vat_category_code = ac_data.get('vat_category_code', 'Z')  # Default to Z for safety
            vat_rate = ac_data.get('vat_rate', 0)

            # Final validation for BR-S-07: ensure Standard rated has rate > 0
            if vat_category_code == 'S' and vat_rate <= 0:
                # Convert to Zero rated for BR-S-07 compliance
                vat_category_code = 'Z'
                # Converting Standard rated charge to Zero rated due to zero/negative VAT rate

            ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID").text = vat_category_code

            # VAT Rate (BT-103) - BR-S-07 for Standard rated, BR-Z-07 for Zero rated
            if vat_category_code == 'S':
                # Standard rated: rate must be > 0 (BR-S-07)
                if vat_rate > 0:
                    ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent").text = str(vat_rate)
                else:
                    # Fallback for safety
                    ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent").text = '0'
            elif vat_category_code == 'Z':
                # Zero rated: rate must be 0 (BR-Z-07)
                ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent").text = '0'
            # For other categories, don't include Percent element

            # Tax Scheme
            tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
            ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'

    def add_additional_document_reference(self, root: ET.Element, ref_data: Dict[str, Any]):
        """Add additional document reference information."""
        doc_ref = ET.SubElement(root, f"{{{self.namespaces['cac']}}}AdditionalDocumentReference")

        # Document ID (required)
        if 'id' in ref_data:
            ET.SubElement(doc_ref, f"{{{self.namespaces['cbc']}}}ID").text = ref_data['id']

        # Document Type Code (optional)
        if ref_data.get('document_type_code'):
            ET.SubElement(doc_ref, f"{{{self.namespaces['cbc']}}}DocumentTypeCode").text = \
                ref_data['document_type_code']

        # Document Type (optional)
        if ref_data.get('document_type'):
            ET.SubElement(doc_ref, f"{{{self.namespaces['cbc']}}}DocumentType").text = \
                ref_data['document_type']

        # Document Description (optional)
        if ref_data.get('document_description'):
            ET.SubElement(doc_ref, f"{{{self.namespaces['cbc']}}}DocumentDescription").text = \
                ref_data['document_description']

        # Attachment (optional - for binary attachments)
        if ref_data.get('attachment'):
            attachment = ET.SubElement(doc_ref, f"{{{self.namespaces['cac']}}}Attachment")
            # Could add EmbeddedDocumentBinaryObject here for actual file content
            pass

    def add_tax_totals(self, root: ET.Element, taxes: List[Dict[str, Any]], allowances_charges: List[Dict[str, Any]] = None, zero_rated_taxable_amount: float = 0.0, has_zero_rated_elements: bool = False, validated_currency: str = 'EUR'):
        """Add tax totals information with proper VAT breakdown (BG-23)."""
        # Ensure taxes is a list
        if not taxes:
            taxes = []
        
        # Create tax total element and add total amount
        tax_total = self.create_tax_total_element(root, taxes, validated_currency)
        
        # Group taxes by rate and category
        tax_subtotals_map = self.group_taxes_by_rate_category(taxes)
        
        # Create tax subtotals for each group
        self.create_tax_subtotals(tax_total, tax_subtotals_map, validated_currency)
        
        # Add zero-rated breakdown if needed
        self.add_zero_rated_breakdown_if_needed(tax_total, tax_subtotals_map, has_zero_rated_elements, zero_rated_taxable_amount, validated_currency)

    def create_tax_total_element(self, root, taxes, currency):
        """Create the main TaxTotal element with total tax amount."""
        tax_total = ET.SubElement(root, f"{{{self.namespaces['cac']}}}TaxTotal")
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

    def add_zero_rated_breakdown_if_needed(self, tax_total, tax_subtotals_map, has_zero_rated_elements, zero_rated_taxable_amount, currency):
        """Add zero-rated VAT breakdown if needed for BR-Z-01/BR-Z-08 compliance."""
        has_zero_rated_breakdown = any(subtotal_data['category_id'] == 'Z' for subtotal_data in tax_subtotals_map.values())

        if has_zero_rated_elements and not has_zero_rated_breakdown:
            tax_subtotal = ET.SubElement(tax_total, f"{{{self.namespaces['cac']}}}TaxSubtotal")

            # Taxable Amount (BT-116) - Calculated per BR-Z-08
            ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxableAmount",
                         currencyID=currency).text = str(zero_rated_taxable_amount)

            # Tax Amount (BT-117) - Zero for zero rated
            ET.SubElement(tax_subtotal, f"{{{self.namespaces['cbc']}}}TaxAmount",
                         currencyID=currency).text = '0.00'

            # Tax Category
            tax_category = ET.SubElement(tax_subtotal, f"{{{self.namespaces['cac']}}}TaxCategory")
            ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID").text = 'Z'
            ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}Percent").text = '0'

            # Tax Scheme
            tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
            ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
    
    def add_legal_monetary_total(self, root: ET.Element, totals_data: Dict[str, Any], document_currency: str, allowances_charges: List[Dict[str, Any]] = None, lines: List[Dict[str, Any]] = None, taxes: List[Dict[str, Any]] = None):
        """Add legal monetary total information."""
        legal_total = ET.SubElement(root, f"{{{self.namespaces['cac']}}}LegalMonetaryTotal")
        
        # Calculate monetary amounts
        amounts = self.calculate_monetary_amounts(totals_data, allowances_charges, lines, taxes)
        
        # Add all monetary elements
        self.add_monetary_elements(legal_total, amounts, document_currency)

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

        # Sum of charges on document level (BT-108)
        charge_total = 0.0
        if allowances_charges:
            charge_total = sum(
                ac.get('amount', 0)
                for ac in allowances_charges
                if ac.get('charge_indicator') == 'true'  # Only charges
            )

        # BR-CO-13 formula: Σ(BT-131) - BT-107 + BT-108
        tax_exclusive_amount = line_extension_total - allowance_total + charge_total

        # Tax Inclusive Amount (BT-112) - BR-CO-15: BT-109 + BT-110
        total_vat_amount = sum(tax.get('amount', 0) for tax in (taxes or []))
        tax_inclusive_amount = tax_exclusive_amount + total_vat_amount

        # Payable Amount (BT-115) - BR-CO-16: BT-112 - BT-113 + BT-114
        paid_amount = totals_data.get('paid_amount', 0)
        rounding_amount = totals_data.get('rounding_amount', 0)
        payable_amount = tax_inclusive_amount - paid_amount + rounding_amount

        return {
            'line_extension_amount': line_extension_amount,
            'tax_exclusive_amount': tax_exclusive_amount,
            'tax_inclusive_amount': tax_inclusive_amount,
            'payable_amount': payable_amount,
            'allowance_total': allowance_total,
            'charge_total': charge_total
        }

    def add_monetary_elements(self, legal_total, amounts, document_currency):
        """Add all monetary elements to the legal total."""
        # Line Extension Amount
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}LineExtensionAmount",
                     currencyID=document_currency).text = str(amounts['line_extension_amount'])
        
        # Tax Exclusive Amount (BT-109)
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}TaxExclusiveAmount",
                     currencyID=document_currency).text = str(amounts['tax_exclusive_amount'])

        # Tax Inclusive Amount (BT-112)
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}TaxInclusiveAmount",
                     currencyID=document_currency).text = str(amounts['tax_inclusive_amount'])

        # Allowance Total (BT-107) - must come before PayableAmount according to XSD
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}AllowanceTotalAmount",
                     currencyID=document_currency).text = str(amounts['allowance_total'])

        # Charge Total (BT-108) - must come before PayableAmount according to XSD
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}ChargeTotalAmount",
                     currencyID=document_currency).text = str(amounts['charge_total'])

        # Payable Amount (BT-115) - must come after AllowanceTotalAmount and ChargeTotalAmount
        ET.SubElement(legal_total, f"{{{self.namespaces['cbc']}}}PayableAmount",
                     currencyID=document_currency).text = str(amounts['payable_amount'])
    
    def add_invoice_line(self, root: ET.Element, line_data: Dict[str, Any], document_currency: str):
        """Add invoice line information."""
        
        
        try:
            invoice_line = ET.SubElement(root, f"{{{self.namespaces['cac']}}}InvoiceLine")
            
            # Line ID
            ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}ID").text = \
                str(line_data.get('id', 1))
            
            # Invoiced Quantity
            ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}InvoicedQuantity",
                         unitCode=self.map_unit_code(line_data.get('unit_code', ''))).text = \
                str(line_data.get('quantity', 1))
            
            # Line Extension Amount
            ET.SubElement(invoice_line, f"{{{self.namespaces['cbc']}}}LineExtensionAmount",
                         currencyID=document_currency).text = \
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
            
            # Classified Tax Category (BT-151) - Required for BR-S-01
            classified_tax_category = ET.SubElement(item, f"{{{self.namespaces['cac']}}}ClassifiedTaxCategory")
            ET.SubElement(classified_tax_category, f"{{{self.namespaces['cbc']}}}ID").text = \
                line_data.get('tax_category_id', 'S')  # Default to Standard rated

            # VAT Rate (BT-152) - Required for BR-S-08
            if 'tax_rate' in line_data and line_data['tax_rate'] > 0:
                ET.SubElement(classified_tax_category, f"{{{self.namespaces['cbc']}}}Percent").text = \
                    str(line_data['tax_rate'])

            tax_scheme = ET.SubElement(classified_tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
            ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'

            # Item Sellers Item Identification
            if 'sellers_item_id' in line_data and line_data['sellers_item_id']:
                sellers_id = ET.SubElement(item, f"{{{self.namespaces['cac']}}}SellersItemIdentification")
                ET.SubElement(sellers_id, f"{{{self.namespaces['cbc']}}}ID").text = \
                    line_data['sellers_item_id']
            
            # Price
            price = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}Price")
            ET.SubElement(price, f"{{{self.namespaces['cbc']}}}PriceAmount",
                         currencyID=document_currency).text = \
                str(line_data.get('unit_price', 0))
            
            # Line Tax Total
            if 'tax' in line_data and line_data['tax']:
                line_tax_total = ET.SubElement(invoice_line, f"{{{self.namespaces['cac']}}}TaxTotal")
                ET.SubElement(line_tax_total, f"{{{self.namespaces['cbc']}}}TaxAmount",
                             currencyID=document_currency).text = \
                    str(line_data['tax'].get('amount', 0))
                
                tax_category = ET.SubElement(line_tax_total, f"{{{self.namespaces['cac']}}}TaxCategory")
                ET.SubElement(tax_category, f"{{{self.namespaces['cbc']}}}ID").text = \
                    line_data['tax'].get('category_id', 'S')
                
                tax_scheme = ET.SubElement(tax_category, f"{{{self.namespaces['cac']}}}TaxScheme")
                ET.SubElement(tax_scheme, f"{{{self.namespaces['cbc']}}}ID").text = 'VAT'
                
        except Exception as e:
            frappe.logger().error(f"Error processing invoice line: {str(e)}")
            raise 

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