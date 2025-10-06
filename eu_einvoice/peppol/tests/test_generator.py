"""
Tests for PEPPOL Generator

This module contains unit tests for the PEPPOL UBL 2.1 XML generator.
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any

from ..generator import PEPPOLGenerator
from ..profiles import PEPPOLProfile


class TestPEPPOLGenerator(unittest.TestCase):
    """Test cases for PEPPOLGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = PEPPOLGenerator(PEPPOLProfile.PEPPOL_BIS_30)
        
        # Sample invoice data
        self.sample_invoice = {
            'invoice_id': 'INV-2024-001',
            'issue_date': '2024-01-15',
            'due_date': '2024-02-15',
            'currency': 'EUR',
            'buyer_reference': 'BUYER-REF-001',
            'supplier': {
                'name': 'Test Supplier BV',
                'legal_name': 'Test Supplier BV',
                'tax_id': 'NL123456789B01',
                'address': {
                    'street': 'Test Street 123',
                    'city': 'Amsterdam',
                    'postal_code': '1000 AA',
                    'country': 'NL'
                }
            },
            'customer': {
                'name': 'Test Customer NV',
                'tax_id': 'BE0123456789',
                'address': {
                    'street': 'Customer Street 456',
                    'city': 'Brussels',
                    'postal_code': '1000',
                    'country': 'BE'
                },
                'contact': {
                    'name': 'John Doe',
                    'email': 'john.doe@customer.com',
                    'telephone': '+32 2 123 45 67'
                }
            },
            'payment': {
                'payment_means_code': '1',
                'due_date': '2024-02-15',
                'payment_id': 'PAY-001',
                'account': 'NL91ABNA0417164300'
            },
            'payment_terms': {
                'note': 'Payment within 30 days',
                'amount': 1000.00
            },
            'taxes': [
                {
                    'amount': 210.00,
                    'taxable_amount': 1000.00,
                    'category_id': 'S',
                    'currency': 'EUR'
                }
            ],
            'totals': {
                'line_extension_amount': 1000.00,
                'tax_exclusive_amount': 1000.00,
                'tax_inclusive_amount': 1210.00,
                'payable_amount': 1210.00,
                'currency': 'EUR'
            },
            'lines': [
                {
                    'line_id': 1,
                    'name': 'Test Product',
                    'description': 'A test product for validation',
                    'quantity': 2,
                    'unit_code': 'C62',
                    'unit_price': 500.00,
                    'line_extension_amount': 1000.00,
                    'currency': 'EUR',
                    'tax': {
                        'amount': 210.00,
                        'category_id': 'S'
                    }
                }
            ]
        }
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        self.assertEqual(self.generator.profile, PEPPOLProfile.PEPPOL_BIS_30)
        self.assertIsNotNone(self.generator.profile_info)
        self.assertIn('ubl', self.generator.namespaces)
        self.assertIn('cbc', self.generator.namespaces)
        self.assertIn('cac', self.generator.namespaces)
    
    def test_generate_invoice_basic(self):
        """Test basic invoice generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        
        # Check that XML is generated
        self.assertIsInstance(xml_content, str)
        self.assertTrue(xml_content.startswith('<?xml'))
        
        # Parse and validate XML structure
        root = ET.fromstring(xml_content)
        self.assertEqual(root.tag, '{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice')
    
    def test_document_header_generation(self):
        """Test document header generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        root = ET.fromstring(xml_content)
        
        # Check CustomizationID
        customization_id = root.find('.//cbc:CustomizationID', 
                                   namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(customization_id)
        self.assertEqual(customization_id.text, self.generator.profile_info.customization_id)
        
        # Check ProfileID
        profile_id = root.find('.//cbc:ProfileID', 
                              namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(profile_id)
        self.assertEqual(profile_id.text, self.generator.profile.value)
        
        # Check Invoice ID
        invoice_id = root.find('.//cbc:ID', 
                              namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(invoice_id)
        self.assertEqual(invoice_id.text, 'INV-2024-001')
        
        # Check Issue Date
        issue_date = root.find('.//cbc:IssueDate', 
                              namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(issue_date)
        self.assertEqual(issue_date.text, '2024-01-15')
        
        # Check Currency
        currency = root.find('.//cbc:DocumentCurrencyCode', 
                            namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(currency)
        self.assertEqual(currency.text, 'EUR')
    
    def test_supplier_party_generation(self):
        """Test supplier party generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        root = ET.fromstring(xml_content)
        
        # Check supplier name
        supplier_name = root.find('.//cac:AccountingSupplierParty//cac:Party//cac:PartyName//cbc:Name',
                                 namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                           'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(supplier_name)
        self.assertEqual(supplier_name.text, 'Test Supplier BV')
        
        # Check supplier tax ID
        supplier_tax_id = root.find('.//cac:AccountingSupplierParty//cac:Party//cac:PartyTaxScheme//cbc:CompanyID',
                                   namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                             'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(supplier_tax_id)
        self.assertEqual(supplier_tax_id.text, 'NL123456789B01')
    
    def test_customer_party_generation(self):
        """Test customer party generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        root = ET.fromstring(xml_content)
        
        # Check customer name
        customer_name = root.find('.//cac:AccountingCustomerParty//cac:Party//cac:PartyName//cbc:Name',
                                 namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                           'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(customer_name)
        self.assertEqual(customer_name.text, 'Test Customer NV')
        
        # Check customer tax ID
        customer_tax_id = root.find('.//cac:AccountingCustomerParty//cac:Party//cac:PartyTaxScheme//cbc:CompanyID',
                                   namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                             'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(customer_tax_id)
        self.assertEqual(customer_tax_id.text, 'BE0123456789')
    
    def test_payment_means_generation(self):
        """Test payment means generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        root = ET.fromstring(xml_content)
        
        # Check payment means code
        payment_code = root.find('.//cbc:PaymentMeansCode', 
                                namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(payment_code)
        self.assertEqual(payment_code.text, '1')
        
        # Check payment account
        payment_account = root.find('.//cac:PayeeFinancialAccount//cbc:ID', 
                                   namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                             'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(payment_account)
        self.assertEqual(payment_account.text, 'NL91ABNA0417164300')
    
    def test_tax_totals_generation(self):
        """Test tax totals generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        root = ET.fromstring(xml_content)
        
        # Check tax amount
        tax_amount = root.find('.//cac:TaxTotal//cbc:TaxAmount', 
                              namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(tax_amount)
        self.assertEqual(tax_amount.text, '210.0')
        
        # Check tax category
        tax_category = root.find('.//cac:TaxCategory//cbc:ID', 
                                namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                          'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(tax_category)
        self.assertEqual(tax_category.text, 'S')
    
    def test_legal_monetary_total_generation(self):
        """Test legal monetary total generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        root = ET.fromstring(xml_content)
        
        # Check payable amount
        payable_amount = root.find('.//cac:LegalMonetaryTotal//cbc:PayableAmount', 
                                  namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(payable_amount)
        self.assertEqual(payable_amount.text, '1210.0')
        
        # Check tax inclusive amount
        tax_inclusive = root.find('.//cac:LegalMonetaryTotal//cbc:TaxInclusiveAmount', 
                                 namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                           'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(tax_inclusive)
        self.assertEqual(tax_inclusive.text, '1210.0')
    
    def test_invoice_line_generation(self):
        """Test invoice line generation."""
        xml_content = self.generator.generate_invoice(self.sample_invoice)
        root = ET.fromstring(xml_content)
        
        # Check line ID
        line_id = root.find('.//cac:InvoiceLine//cbc:ID', 
                           namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                     'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(line_id)
        self.assertEqual(line_id.text, '1')
        
        # Check item name
        item_name = root.find('.//cac:InvoiceLine//cac:Item//cbc:Name', 
                             namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                       'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(item_name)
        self.assertEqual(item_name.text, 'Test Product')
        
        # Check quantity
        quantity = root.find('.//cac:InvoiceLine//cbc:InvoicedQuantity', 
                            namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                      'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        self.assertIsNotNone(quantity)
        self.assertEqual(quantity.text, '2')
        self.assertEqual(quantity.get('unitCode'), 'C62')
    
    def test_minimal_invoice_generation(self):
        """Test generation with minimal required data."""
        minimal_invoice = {
            'invoice_id': 'MIN-001',
            'supplier': {'name': 'Minimal Supplier'},
            'customer': {'name': 'Minimal Customer'},
            'totals': {
                'line_extension_amount': 100.00,
                'tax_exclusive_amount': 100.00,
                'tax_inclusive_amount': 121.00,
                'payable_amount': 121.00,
                'currency': 'EUR'
            },
            'lines': [
                {
                    'line_id': 1,
                    'name': 'Minimal Item',
                    'quantity': 1,
                    'unit_price': 100.00,
                    'line_extension_amount': 100.00,
                    'currency': 'EUR'
                }
            ]
        }
        
        xml_content = self.generator.generate_invoice(minimal_invoice)
        self.assertIsInstance(xml_content, str)
        self.assertTrue(xml_content.startswith('<?xml'))
        
        # Parse and check basic structure
        root = ET.fromstring(xml_content)
        self.assertEqual(root.tag, '{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice')


if __name__ == '__main__':
    unittest.main() 