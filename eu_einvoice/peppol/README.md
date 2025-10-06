# PEPPOL BIS Billing 3.0 Implementation

This package provides a complete implementation of PEPPOL BIS Billing 3.0 for ERPNext, enabling businesses to generate and validate PEPPOL-compliant e-invoices using the official OpenPEPPOL specifications.

## Architecture

The implementation follows a modular architecture with clear separation of concerns:

### Core Components

- **`generator.py`**: Converts ERPNext invoice data to UBL 2.1 XML
- **`validator.py`**: XSD validation (lxml, xmlschema) and Schematron validation (Saxon/Che or lxml+schematron)
- **`codelist.py`**: Loads and queries code lists from official PEPPOL repository
- **`profiles.py`**: Handles profile/CIUS logic and country-specific requirements
- **`utils.py`**: Utility classes for validation results and common functionality
- **`core.py`**: High-level integration and orchestration
- **`tests/`**: Unit tests using official examples
- **`README.md`**: Usage, architecture, and compliance notes

### Key Features

- **UBL 2.1 XML Generation**: Complete UBL 2.1 invoice generation with proper namespaces
- **Official Validation**: Uses official PEPPOL Schematron rules and XSD schemas
- **Code List Compliance**: Validates against official PEPPOL code lists
- **Business Rules**: Implements PEPPOL business rules (BR-01 to BR-67)
- **Multi-Country Support**: Supports country-specific CIUS profiles
- **XSLT 3.0 Support**: Uses Saxon-HE for advanced XSLT processing
- **Error Reporting**: Detailed validation error reporting with context

## Installation

### Prerequisites

```bash
# Install required Python packages
pip install lxml saxonche xmlschema

# For development
pip install pytest pytest-cov
```

### Setup

1. **Clone the official PEPPOL repository**:
   ```bash
   cd apps/eu_einvoice/eu_einvoice/peppol/
   git clone https://github.com/OpenPEPPOL/peppol-bis-invoice-3.git
   ```

2. **Verify structure**:
   ```
   peppol/
   ├── peppol-bis-invoice-3/
   │   ├── rules/
   │   │   └── PEPPOL-UBL-2.1-validation.xslt
   │   ├── structure/
   │   │   ├── codelist/
   │   │   └── xsd/
   │   └── examples/
   ├── generator.py
   ├── validator.py
   ├── codelist.py
   ├── profiles.py
   ├── utils.py
   └── core.py
   ```

## Usage

### Basic Usage

```python
from eu_einvoice.peppol import PEPPOLGenerator, PEPPOLValidator, PEPPOLProfile

# Initialize generator
generator = PEPPOLGenerator(PEPPOLProfile.PEPPOL_BIS_30)

# Sample invoice data
invoice_data = {
    'invoice_id': 'INV-2024-001',
    'issue_date': '2024-01-15',
    'currency': 'EUR',
    'supplier': {
        'name': 'Test Supplier BV',
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
        }
    },
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
            'quantity': 2,
            'unit_code': 'C62',
            'unit_price': 500.00,
            'line_extension_amount': 1000.00,
            'currency': 'EUR'
        }
    ]
}

# Generate UBL XML
ubl_xml = generator.generate_invoice(invoice_data)

# Validate the generated XML
validator = PEPPOLValidator(PEPPOLProfile.PEPPOL_BIS_30)
validation_result = validator.validate(ubl_xml)

if validation_result.is_valid:
    print("✅ Invoice is PEPPOL compliant!")
else:
    print("❌ Validation errors found:")
    for error in validation_result.errors:
        print(f"  - {error.rule_id}: {error.message}")
```

### Advanced Usage

#### Code List Management

```python
from eu_einvoice.peppol import code_list_manager

# Load all code lists
results = code_list_manager.load_all_code_lists()

# Check if a code is valid
is_valid = code_list_manager.is_valid_code('PaymentMeansCode', '1')
print(f"Payment means code '1' is valid: {is_valid}")

# Get code description
description = code_list_manager.get_code_description('PaymentMeansCode', '1', 'en')
print(f"Description: {description}")

# Export code list
json_export = code_list_manager.export_code_list('PaymentMeansCode', 'json')
```

#### Profile Management

```python
from eu_einvoice.peppol import get_profile_info, get_available_profiles

# Get available profiles
profiles = get_available_profiles()
print(f"Available profiles: {profiles}")

# Get profile information
profile_info = get_profile_info(PEPPOLProfile.PEPPOL_BIS_30)
print(f"Profile: {profile_info.name}")
print(f"Customization ID: {profile_info.customization_id}")
```

#### Validation with Details

```python
from eu_einvoice.peppol import PEPPOLValidator

validator = PEPPOLValidator(PEPPOLProfile.PEPPOL_BIS_30)
result = validator.validate(ubl_xml)

# Get validation summary
summary = validator.get_validation_summary(result)
print(f"Validation time: {summary['validation_time']:.2f}s")
print(f"Total rules checked: {summary['total_rules_checked']}")
print(f"Errors: {summary['error_count']}")
print(f"Warnings: {summary['warning_count']}")

# Detailed error analysis
for error in result.errors:
    print(f"Rule: {error.rule_id}")
    print(f"Message: {error.message}")
    print(f"Context: {error.context}")
    print(f"Line: {error.line_number}")
    print("---")
```

## Configuration

### Profile Configuration

Profiles are defined in `profiles.py` and include:

- **PEPPOL_BIS_30**: Standard PEPPOL BIS Billing 3.0
- **PEPPOL_BIS_30_NL**: Netherlands CIUS
- **PEPPOL_BIS_30_BE**: Belgium CIUS
- **PEPPOL_BIS_30_DE**: Germany CIUS

### Code List Configuration

Code lists are automatically loaded from the official PEPPOL repository structure:

```
peppol-bis-invoice-3/structure/codelist/
├── CurrencyCode.xml
├── DocumentTypeCode.xml
├── PaymentMeansCode.xml
├── TaxCategoryCode.xml
├── UnitCode.xml
└── CountryCode.xml
```

## Testing

### Run Tests

```bash
# Run all tests
python -m pytest apps/eu_einvoice/eu_einvoice/peppol/tests/

# Run specific test file
python -m pytest apps/eu_einvoice/eu_einvoice/peppol/tests/test_generator.py

# Run with coverage
python -m pytest --cov=eu_einvoice.peppol apps/eu_einvoice/eu_einvoice/peppol/tests/
```

### Test Examples

The test suite includes:

- **Generator Tests**: UBL XML generation validation
- **Validator Tests**: Schematron and XSD validation
- **Code List Tests**: Code list loading and validation
- **Integration Tests**: End-to-end workflow testing

## Compliance

### PEPPOL BIS Billing 3.0 Compliance

This implementation is designed to be fully compliant with:

- **PEPPOL BIS Billing 3.0** specification
- **UBL 2.1** XML schema
- **EN 16931** European standard
- **Official PEPPOL Schematron rules**
- **PEPPOL code lists**

### Validation Levels

1. **XML Structure**: Basic XML well-formedness
2. **XSD Validation**: UBL 2.1 schema compliance
3. **Schematron Validation**: Business rules (BR-01 to BR-67)
4. **Code List Validation**: Official code list compliance
5. **Business Logic**: Custom business rule validation

## Error Handling

### Validation Errors

The validator provides detailed error information:

```python
class ValidationMessage:
    rule_id: str          # Rule identifier (e.g., "BR-1")
    severity: str          # "error", "warning", or "info"
    message: str          # Human-readable error message
    context: str          # XML context where error occurred
    line_number: int      # XML line number
    column_number: int    # XML column number
    test_expression: str  # Schematron test expression
    details: dict         # Additional error details
```

### Common Error Types

- **BR-1**: Missing invoice number
- **BR-2**: Missing issue date
- **BR-3**: Missing invoice type code
- **BR-4**: Missing currency code
- **BR-5**: Missing seller name
- **BR-6**: Missing buyer name
- **BR-7**: Missing total amount
- **BR-8**: Missing payable amount

## Deployment

### Production Setup

1. **Install dependencies**:
   ```bash
   pip install lxml saxonche xmlschema
   ```

2. **Download official resources**:
   ```bash
   cd apps/eu_einvoice/eu_einvoice/peppol/
   git clone https://github.com/OpenPEPPOL/peppol-bis-invoice-3.git
   ```

3. **Verify installation**:
   ```python
   from eu_einvoice.peppol import PEPPOLGenerator, PEPPOLValidator
   
   # Test basic functionality
   generator = PEPPOLGenerator()
   validator = PEPPOLValidator()
   print("✅ PEPPOL implementation ready!")
   ```

### Performance Considerations

- **Code List Caching**: Code lists are loaded once and cached in memory
- **Validation Optimization**: Schematron compilation is cached
- **Memory Management**: Large XML documents are processed efficiently
- **Error Reporting**: Minimal overhead for validation reporting

## Support

### Documentation

- **PEPPOL BIS Billing 3.0**: [Official Specification](https://docs.peppol.eu/poacc/billing/3.0/)
- **UBL 2.1**: [OASIS Standard](https://docs.oasis-open.org/ubl/os-UBL-2.1/)
- **EN 16931**: [European Standard](https://www.cen.eu/work/areas/ICT/eBusiness/Pages/default.aspx)

### Community

- **OpenPEPPOL**: [Official Repository](https://github.com/OpenPEPPOL/peppol-bis-invoice-3)
- **ERPNext**: [Community Forum](https://discuss.erpnext.com/)
- **Issues**: Report bugs and feature requests via GitHub issues

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This implementation is part of the EU E-Invoice app for ERPNext and follows the same licensing terms as ERPNext.