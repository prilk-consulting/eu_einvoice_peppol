#!/usr/bin/env python3
"""
PEPPOL BIS Billing 3.0 Example

This script demonstrates how to use the PEPPOL implementation
to generate and validate UBL 2.1 XML invoices.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import the peppol module
sys.path.insert(0, str(Path(__file__).parent.parent))

from peppol import (
    PEPPOLGenerator, 
    PEPPOLValidator, 
    PEPPOLProfile,
    code_list_manager,
    get_profile_info
)


def create_sample_invoice_data():
    """Create sample invoice data for demonstration."""
    
    return {
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


def demonstrate_generation():
    """Demonstrate UBL XML generation."""
    
    print("🔧 Demonstrating PEPPOL UBL XML Generation")
    print("=" * 50)
    
    # Initialize generator
    generator = PEPPOLGenerator(PEPPOLProfile.PEPPOL_BIS_30)
    print(f"✅ Generator initialized with profile: {generator.profile.value}")
    
    # Create sample data
    invoice_data = create_sample_invoice_data()
    print(f"✅ Sample invoice data created: {invoice_data['invoice_id']}")
    
    # Generate UBL XML
    try:
        ubl_xml = generator.generate_invoice(invoice_data)
        print(f"✅ UBL XML generated successfully ({len(ubl_xml)} characters)")
        
        # Save to file for inspection
        output_file = Path(__file__).parent / "generated_invoice.xml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ubl_xml)
        print(f"✅ XML saved to: {output_file}")
        
        return ubl_xml
        
    except Exception as e:
        print(f"❌ Error generating XML: {e}")
        return None


def demonstrate_validation(ubl_xml):
    """Demonstrate UBL XML validation."""
    
    print("\n🔍 Demonstrating PEPPOL Validation")
    print("=" * 50)
    
    # Initialize validator
    validator = PEPPOLValidator(PEPPOLProfile.PEPPOL_BIS_30)
    print(f"✅ Validator initialized with profile: {validator.profile.value}")
    
    # Validate XML
    try:
        validation_result = validator.validate(ubl_xml)
        print(f"✅ Validation completed in {validation_result.validation_time:.2f}s")
        
        # Display results
        if validation_result.is_valid:
            print("✅ Invoice is PEPPOL compliant!")
        else:
            print("❌ Validation errors found:")
            for error in validation_result.errors:
                print(f"  - {error.rule_id}: {error.message}")
        
        # Show summary
        summary = validator.get_validation_summary(validation_result)
        print(f"\n📊 Validation Summary:")
        print(f"  - Total rules checked: {summary['total_rules_checked']}")
        print(f"  - Errors: {summary['error_count']}")
        print(f"  - Warnings: {summary['warning_count']}")
        print(f"  - Info messages: {summary['info_count']}")
        
        return validation_result
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return None


def demonstrate_code_lists():
    """Demonstrate code list functionality."""
    
    print("\n📋 Demonstrating Code List Management")
    print("=" * 50)
    
    try:
        # Load code lists
        results = code_list_manager.load_all_code_lists()
        print(f"✅ Loaded {len(results)} code list files")
        
        # Show loaded code lists
        loaded_lists = code_list_manager.get_loaded_code_lists()
        print(f"📋 Loaded code lists: {', '.join(loaded_lists)}")
        
        # Test code validation
        test_codes = [
            ('PaymentMeansCode', '1'),
            ('CurrencyCode', 'EUR'),
            ('DocumentTypeCode', '380'),
            ('UnitCode', 'C62')
        ]
        
        print("\n🔍 Code Validation Tests:")
        for code_list_id, code in test_codes:
            is_valid = code_list_manager.is_valid_code(code_list_id, code)
            description = code_list_manager.get_code_description(code_list_id, code, 'en')
            status = "✅" if is_valid else "❌"
            print(f"  {status} {code_list_id}:{code} - {description}")
        
        # Show code list summary
        summary = code_list_manager.get_code_list_summary()
        print(f"\n📊 Code List Summary:")
        print(f"  - Total loaded: {summary['total_loaded']}")
        for code_list_id, info in summary['code_lists'].items():
            print(f"  - {code_list_id}: {info['codes_count']} codes")
        
    except Exception as e:
        print(f"❌ Error with code lists: {e}")


def demonstrate_profiles():
    """Demonstrate profile functionality."""
    
    print("\n🏷️ Demonstrating Profile Management")
    print("=" * 50)
    
    try:
        # Get profile information
        profile_info = get_profile_info(PEPPOLProfile.PEPPOL_BIS_30)
        print(f"✅ Profile: {profile_info.name}")
        print(f"  - Customization ID: {profile_info.customization_id}")
        print(f"  - Description: {profile_info.description}")
        print(f"  - Schematron file: {profile_info.schematron_file}")
        
        # Show available profiles
        from peppol.profiles import get_available_profiles
        profiles = get_available_profiles()
        print(f"\n📋 Available profiles:")
        for profile in profiles:
            print(f"  - {profile.value}: {profile.name}")
        
    except Exception as e:
        print(f"❌ Error with profiles: {e}")


def main():
    """Main demonstration function."""
    
    print("🚀 PEPPOL BIS Billing 3.0 Implementation Demo")
    print("=" * 60)
    
    # Check if official repository is available
    repo_path = Path(__file__).parent / "peppol-bis-invoice-3"
    if not repo_path.exists():
        print("⚠️  Official PEPPOL repository not found!")
        print("   Please clone it first:")
        print("   cd apps/eu_einvoice/eu_einvoice/peppol/")
        print("   git clone https://github.com/OpenPEPPOL/peppol-bis-invoice-3.git")
        print()
    
    # Demonstrate each component
    ubl_xml = demonstrate_generation()
    
    if ubl_xml:
        demonstrate_validation(ubl_xml)
    
    demonstrate_code_lists()
    demonstrate_profiles()
    
    print("\n🎉 Demo completed!")
    print("\n📝 Next steps:")
    print("  1. Review the generated XML file")
    print("  2. Run the test suite: python -m pytest tests/")
    print("  3. Integrate with your ERPNext installation")
    print("  4. Configure country-specific profiles")


if __name__ == "__main__":
    main() 