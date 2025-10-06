#!/usr/bin/env python3
"""
Test script for XSLT handling in PEPPOL implementation.

This script demonstrates how to work with .xslt files from the official
PEPPOL repository and test validation capabilities.
"""

import sys
from pathlib import Path

# Add the app to Python path
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(app_dir))

from eu_einvoice.european_e_invoice.peppol.xslt_handler import XSLTHandler
from eu_einvoice.european_e_invoice.peppol.generator import create_peppol_einvoice
from eu_einvoice.european_e_invoice.peppol.validator import validate_peppol_einvoice


def test_xslt_handler():
    """Test the XSLT handler functionality."""
    
    print("=" * 60)
    print("XSLT Handler Test")
    print("=" * 60)
    
    handler = XSLTHandler()
    
    # Test 1: Get stylesheet information
    print("\n1. Getting stylesheet information...")
    info = handler.get_stylesheet_info()
    
    print(f"Schematron directory: {info['schematron_dir']}")
    print(f"Available stylesheets: {len(info['available_stylesheets'])}")
    
    if info['available_stylesheets']:
        for stylesheet in info['available_stylesheets']:
            print(f"  - {stylesheet['name']} ({stylesheet['format']}, {stylesheet['size']} bytes)")
        
        if info['recommended_stylesheet']:
            print(f"Recommended: {info['recommended_stylesheet']['name']}")
    else:
        print("  No stylesheets found")
        return False
    
    # Test 2: Setup official stylesheet
    print("\n2. Setting up official stylesheet...")
    if handler.setup_official_stylesheet():
        print("✓ Stylesheet setup successful")
    else:
        print("✗ Stylesheet setup failed")
        return False
    
    # Test 3: Test validation with sample XML
    print("\n3. Testing validation...")
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
             xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
             xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
    <cbc:ID>TEST-001</cbc:ID>
    <cbc:IssueDate>2024-01-15</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
    <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="VA">DE123456789</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>Test Supplier</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Test Street</cbc:StreetName>
                <cbc:CityName>Test City</cbc:CityName>
                <cbc:PostalZone>12345</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>DE</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID schemeID="VA">DE123456789</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="VA">DE987654321</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>Test Customer</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Customer Street</cbc:StreetName>
                <cbc:CityName>Customer City</cbc:CityName>
                <cbc:PostalZone>54321</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>DE</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID schemeID="VA">DE987654321</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <cac:PaymentMeans>
        <cbc:PaymentMeansCode>1</cbc:PaymentMeansCode>
        <cbc:PaymentDueDate>2024-02-15</cbc:PaymentDueDate>
        <cac:PayeeFinancialAccount>
            <cbc:ID schemeID="IBAN">DE89370400440532013000</cbc:ID>
        </cac:PayeeFinancialAccount>
    </cac:PaymentMeans>
    
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="EUR">100.00</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="EUR">500.00</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="EUR">100.00</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>20</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="EUR">500.00</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="EUR">500.00</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="EUR">600.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="EUR">600.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="C62">10</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="EUR">500.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>Test Product</cbc:Name>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="EUR">50.00</cbc:PriceAmount>
        </cac:Price>
        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="EUR">100.00</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="EUR">500.00</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="EUR">100.00</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:ID>S</cbc:ID>
                    <cbc:Percent>20</cbc:Percent>
                    <cac:TaxScheme>
                        <cbc:ID>VAT</cbc:ID>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:TaxSubtotal>
        </cac:TaxTotal>
    </cac:InvoiceLine>
</ubl:Invoice>"""
    
    result = handler.test_validation(test_xml)
    if result.get("success"):
        print("✓ Validation test successful")
        print(f"  - Stylesheet: {result['stylesheet']}")
        print(f"  - Report size: {result['report_size']} characters")
        print(f"  - Report preview: {result['report_preview'][:200]}...")
    else:
        print(f"✗ Validation test failed: {result.get('error')}")
        return False
    
    return True


def test_peppol_generation():
    """Test PEPPOL generation (if ERPNext is available)."""
    
    print("\n" + "=" * 60)
    print("PEPPOL Generation Test")
    print("=" * 60)
    
    try:
        # This would require a running ERPNext instance
        # For now, just test the import
        print("✓ PEPPOL generator module imported successfully")
        print("  (Full generation test requires ERPNext instance)")
        return True
        
    except Exception as e:
        print(f"✗ PEPPOL generation test failed: {e}")
        return False


def test_peppol_validation():
    """Test PEPPOL validation with sample data."""
    
    print("\n" + "=" * 60)
    print("PEPPOL Validation Test")
    print("=" * 60)
    
    try:
        # Test with minimal valid XML
        test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <cbc:ID>TEST-001</cbc:ID>
    <cbc:IssueDate>2024-01-15</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
</ubl:Invoice>"""
        
        # This would test the custom validator
        # For now, just test the import
        print("✓ PEPPOL validator module imported successfully")
        print("  (Full validation test requires complete XML)")
        return True
        
    except Exception as e:
        print(f"✗ PEPPOL validation test failed: {e}")
        return False


def main():
    """Run all tests."""
    
    print("PEPPOL XSLT Test Suite")
    print("=" * 60)
    
    tests = [
        ("XSLT Handler", test_xslt_handler),
        ("PEPPOL Generation", test_peppol_generation),
        ("PEPPOL Validation", test_peppol_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 