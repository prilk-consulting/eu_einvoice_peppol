# Copyright (c) 2025, Prilk Consulting BV and contributors
"""
PEPPOL Validator

This module provides UBL 2.1 XML validation for PEPPOL BIS Billing 3.0
compliant invoices from ERPNext data.
"""
import frappe
from pathlib import Path
from typing import Optional


class PEPPOLValidator:
    # PEPPOL XML and XSD validation utilities
    
    def validate_xml_structure(self, xml_bytes: bytes) -> bytes:
        # Validate XML structure (basic well-formedness)
        from lxml import etree
        
        try:
            parser = etree.XMLParser()  # Basic XML parser (validates XML structure)
            root = etree.fromstring(xml_bytes, parser)
            # Return validated XML with pretty formatting
            return etree.tostring(
                root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
            )
        except etree.XMLSyntaxError as e:
            error_msg = f"PEPPOL XML structure validation failed: {str(e)}"
            frappe.log_error(error_msg, "PEPPOL XML Validation")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"PEPPOL XML parsing failed: {str(e)}"
            frappe.log_error(error_msg, "PEPPOL XML Validation")
            raise ValueError(error_msg)

    def validate_xml_against_xsd(self, xml_bytes: bytes, schema: str) -> bytes:
        # Validate XML against XSD schema
        from lxml import etree
        
        # Load XSD schema
        xsd_schema = self.load_xsd_schema(schema)
        if xsd_schema is None:
            return xml_bytes
        
        # Parse and validate XML
        return self.parse_and_validate_xml(xml_bytes, xsd_schema)

    def load_xsd_schema(self, schema: str) -> Optional:
        # Load and compile XSD schema file
        from lxml import etree
        
        # XSD schema path
        schema_dir = Path(__file__).parent / "UBL-2.1" / "xsdrt" / "maindoc"
        schema_file = schema_dir / f"{schema}.xsd"
        
        if not schema_file.exists():
            frappe.log_error(f"PEPPOL XSD schema not found: {schema_file}. Skipping XSD validation.", "PEPPOL XSD Validation")
            return None
        
        try:
            schema_doc = etree.parse(str(schema_file))
            return etree.XMLSchema(schema_doc)
        except Exception as e:
            error_msg = f"PEPPOL XSD schema load failed for {schema}: {str(e)}"
            frappe.log_error(error_msg, "PEPPOL XSD Validation")
            return None

    def parse_and_validate_xml(self, xml_bytes: bytes, xsd_schema) -> bytes:
        # Parse XML with XSD schema validation
        from lxml import etree
        
        try:
            parser = etree.XMLParser(schema=xsd_schema)
            xml_root = etree.fromstring(xml_bytes, parser)
            
            # Return validated XML with pretty formatting
            return etree.tostring(
                xml_root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
            )
        except etree.XMLSchemaError as e:
            error_msg = f"PEPPOL XSD validation failed: {str(e)}"
            frappe.log_error(error_msg, "PEPPOL XSD Validation")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"PEPPOL XML parsing/validation failed: {str(e)}"
            frappe.log_error(error_msg, "PEPPOL XSD Validation")
            raise

