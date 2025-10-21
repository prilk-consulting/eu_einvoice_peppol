# PEPPOL BIS Billing 3.0 Implementation

This package provides a complete implementation of PEPPOL BIS Billing 3.0 for ERPNext, enabling businesses to generate and validate PEPPOL-compliant e-invoices using the official OpenPEPPOL specifications.

## Architecture

The implementation follows a modular architecture with clear separation of concerns:

### Core Components

- **`generator.py`**: Converts ERPNext invoice data to UBL 2.1 XML
- **`b2brouter_api.py`**: B2B Router API client for PEPPOL transmission
- **`profiles.py`**: Handles profile/CIUS logic and country-specific requirements
- **`setup_peppol_codes.py`**: Sets up PEPPOL code lists and mappings
- **`README.md`**: Usage, architecture, and compliance notes

### Key Features

- **UBL 2.1 XML Generation**: Complete UBL 2.1 invoice generation with proper namespaces
- **B2B Router Integration**: Direct transmission to PEPPOL network via API
- **Code List Compliance**: Uses official PEPPOL code lists from ERPNext EDI module
- **Business Rules**: Implements PEPPOL business rules (BR-01 to BR-67)
- **Multi-Country Support**: Supports country-specific CIUS profiles
- **Status Tracking**: Real-time transmission status monitoring
- **Error Handling**: Comprehensive transmission error handling and retry logic

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
   ├── peppol-bis-invoice-3/           # Official PEPPOL repository
   │   ├── rules/
   │   │   ├── sch/                    # Source schematron files
   │   │   │   ├── CEN-EN16931-UBL.sch
   │   │   │   └── PEPPOL-EN16931-UBL.sch
   │   │   └── xsl/                    # Generated XSL validation files
   │   │       ├── CEN-EN16931-UBL.xsl
   │   │       └── PEPPOL-EN16931-UBL.xsl
   │   ├── structure/
   │   │   ├── codelist/
   │   │   └── xsd/
   │   └── examples/
   ├── generator.py                     # PEPPOL XML generator
   ├── b2brouter_api.py                 # B2B Router API client
   ├── profiles.py                      # Profile/CIUS management
   └── setup_peppol_codes.py           # Code list setup
   ```

3. **XSL Validation Files**: The schematron files are manually compiled to XSL for validation using XSLT 1.0 compatible transformations.

## Usage

### Basic Usage

```python
from eu_einvoice.peppol.generator import PEPPOLGenerator
from eu_einvoice.peppol.b2brouter_api import get_b2b_router_client
from eu_einvoice.peppol.profiles import get_profile_info

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
ubl_xml = generator.create_einvoice(invoice_data)

# Transmit to B2B Router (if configured)
try:
    b2b_client = get_b2b_router_client()
    result = b2b_client.transmit_invoice(ubl_xml)
    print(f"✅ Invoice transmitted successfully: {result.get('id')}")
except Exception as e:
    print(f"❌ Transmission failed: {str(e)}")
```

### Advanced Usage

#### Code List Management

Code lists are managed through the ERPNext EDI module using `CommonCodeRetriever`, following the same pattern as the CII/Factur-X implementation.

```python
from eu_einvoice.common_codes import CommonCodeRetriever

# VAT category codes (same as EInvoiceGenerator)
vat_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNCL5305"], "S")
category_code = vat_codes.get([
    ("Tax Category", "Standard Rate"),
    ("Sales Taxes and Charges Template", "VAT 19%")
])
print(f"VAT category code: {category_code}")  # Output: "S"

# Unit of measure codes
uom_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNECERec20"], "C62")
uom_code = uom_codes.get([("UOM", "Piece")])
print(f"UOM code: {uom_code}")  # Output: "C62"

# Country codes
country_codes = CommonCodeRetriever(["urn:peppol:id:codelist:ISO3166-1_Alpha2"], "DE")
country_code = country_codes.get([("Country", "Germany")])
print(f"Country code: {country_code}")  # Output: "DE"
```

#### Profile Management

```python
from eu_einvoice.peppol.profiles import get_profile_info, get_available_profiles

# Get available profiles
profiles = get_available_profiles()
print(f"Available profiles: {profiles}")

# Get profile information
profile_info = get_profile_info(PEPPOLProfile.PEPPOL_BIS_30)
print(f"Profile: {profile_info.name}")
print(f"Customization ID: {profile_info.customization_id}")
```

#### Transmission Status Checking

```python
from eu_einvoice.peppol.b2brouter_api import get_b2b_router_client

# Get B2B Router client
b2b_client = get_b2b_router_client()

# Check transmission status
status = b2b_client.get_invoice_status("transmission_id_here")
print(f"Status: {status.get('status')}")
print(f"Recipient: {status.get('recipient_status')}")
print(f"Delivery time: {status.get('delivery_timestamp')}")

# Get transmission history
history = b2b_client.get_invoice_history("transmission_id_here")
for event in history.get('events', []):
    print(f"{event['timestamp']}: {event['status']} - {event['message']}")
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
- **B2B Router API Tests**: Transmission and status checking functionality
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

### Transmission Process

1. **XML Generation**: Create PEPPOL-compliant UBL 2.1 XML
2. **Authentication**: Connect to B2B Router using API key
3. **Transmission**: Send XML to B2B Router API
4. **Status Tracking**: Monitor delivery status
5. **Error Handling**: Process and handle transmission failures

## Error Handling

### Transmission Errors

B2B Router API errors are handled through structured error responses:

- **Authentication errors**: Invalid API key or permissions
- **Validation errors**: Invalid XML format or missing required fields
- **Network errors**: Connection timeouts or service unavailability
- **Rate limiting**: Too many requests within time window

### Status Monitoring

Track transmission status through the B2B Router dashboard or API:

- **Status values**: `received`, `processing`, `delivered`, `failed`
- **Delivery confirmation**: Timestamp when recipient acknowledges receipt
- **Error details**: Specific failure reasons when transmission fails

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
   from eu_einvoice.peppol.generator import PEPPOLGenerator
   from eu_einvoice.peppol.b2brouter_api import get_b2b_router_client

   # Test basic functionality
   generator = PEPPOLGenerator()
   print("✅ PEPPOL XML generator ready!")

   # Test B2B Router client (if configured)
   try:
       b2b_client = get_b2b_router_client()
       print("✅ B2B Router client ready!")
   except Exception as e:
       print(f"⚠️  B2B Router not configured: {str(e)}")
   ```

### Performance Considerations

- **Code List Caching**: Code lists are loaded once and cached in memory
- **XML Generation**: Efficient UBL 2.1 XML creation with minimal memory usage
- **API Rate Limiting**: Built-in handling of B2B Router rate limits
- **Status Monitoring**: Lightweight status checking without full XML reprocessing

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

Get Accounts : 


B2b Router API

import requests

url = "https://app-staging.b2brouter.net/accounts?offset=0&limit=25"

headers = {
    "accept": "application/json",
    "X-B2B-API-Key": "db89fe23af56f6e8f1d8f8b6ce321d97a6a06a60"
}

response = requests.get(url, headers=headers)

print(response.text)


{
  "accounts": [
    {
      "id": 122305,
      "tin_value": "NL862323459B01",
      "tin_scheme": 9944,
      "cin_value": "82066477",
      "cin_scheme": 106,
      "name": "Prilk Consulting BV",
      "address": "Reykjavikstraat 1",
      "address2": null,
      "city": "Utrecht",
      "postalcode": "3543 KH",
      "province": "Netherlands",
      "country": "nl",
      "currency": "EUR",
      "contact_person": null,
      "phone": null,
      "email": "preetam@prilk.com",
      "rounding_method": "half_up",
      "round_before_sum": false,
      "apply_taxes_per_line": false,
      "registered_for_empl_tax": false,
      "transport_type_code": null,
      "document_type_code": null,
      "has_logo": false,
      "archived": false,
      "created_at": "2025-10-09T07:46:28.000Z",
      "updated_at": "2025-10-13T07:23:50.000Z",
      "transactions_count": 0,
      "transactions_count_previous_period": 0,
      "transactions_limit": 100
    }
  ],
  "total_count": 1,
  "offset": 0,
  "limit": 25
}


Get Transports:
import requests

url = "https://app-staging.b2brouter.net/accounts/122305/transports?offset=0&limit=25"

headers = {
    "accept": "application/json",
    "X-B2B-API-Key": "db89fe23af56f6e8f1d8f8b6ce321d97a6a06a60"
}

response = requests.get(url, headers=headers)

print(response.text)


{
  "transports": [
    {
      "code": "peppol",
      "enabled": true,
      "reception": false,
      "standard_documents": false,
      "invoice": true,
      "credit_note": true,
      "order": true,
      "application_response": true,
      "pin_scheme": 9944,
      "pin_value": "NL862323459B01",
      "created_at": "2025-10-10T12:06:27.361Z",
      "updated_at": "2025-10-10T12:19:43.806Z"
    }
  ],
  "total_count": 1,
  "offset": 0,
  "limit": 25
}

Create Invoice

import requests

url = "https://app-staging.b2brouter.net/projects/122305/invoices.xml"

payload = {
    "send_after_import": True,
    "ack": False,
    "invoice": {
        "type": "IssuedInvoice",
        "number": "3",
        "series_code": "S01",
        "contact_id": 123,
        "contact": {
            "name": "Buyer Full Name AS",
            "tin_scheme": "string",
            "tin_value": "ESA13585625",
            "cin_scheme": 88,
            "cin_value": 7080000950171,
            "address": "Lausitzer Str. 65",
            "address2": "Lausitzer Str. 66",
            "postalcode": "80535",
            "city": "Berlin",
            "province": "Berlin",
            "country": "de",
            "email": "example@email.com",
            "pin_value": "987654321",
            "pin_scheme": "0192",
            "party_identification": "506001234999"
        },
        "date": "2020-11-12",
        "due_date": "2021-01-04",
        "tax_point_date": "2022-02-01",
        "invoicing_period_start": "2024-07-07",
        "invoicing_period_end": "2024-07-07",
        "buyer_reference": "321654",
        "file_reference": "PID33",
        "ponumber": "123",
        "sales_order_reference": "123",
        "receiving_advice_reference": "123",
        "lot_reference": "321654",
        "contract_number": "123Contractref",
        "party_identification": "506001234999",
        "delivery_note_number": "321654",
        "delivery_note_date": "2024-07-07",
        "buyer_accounting_reference": "string",
        "customer_contact_person": "John Doe",
        "language": "en",
        "amended_number": "123",
        "amended_date": "2024-01-01",
        "amended_invoicing_period_start": "2024-01-01",
        "amended_invoicing_period_end": "2024-01-30",
        "amend_reason": "01",
        "correction_method": "01",
        "adjustment_in_cents": 2,
        "charge_amount": 363.5,
        "charge_percent": 20,
        "charge_reason": "Charge",
        "discount_amount": 20,
        "discount_percent": 20,
        "discount_text": "Discount",
        "currency": "EUR",
        "amounts_withheld_reason": "Withheld",
        "withheld_percent": 10,
        "amounts_withheld": 36.35,
        "payments_on_account": 327.15,
        "payment_method": 4,
        "payment_method_text": "Bank transfer",
        "payment_terms": "Payment terms",
        "bank_assigned_creditor_reference": "ES6000000000000000000000",
        "remittance_information": "Remittance information",
        "mandate_reference_identifier": "321654",
        "bank_account_id": 402,
        "bank_account": {
            "type": "iban",
            "number": 10000000000000000000,
            "iban": "ES6000000000000000000000",
            "bic": 0
        },
        "contact_iban": "ES6000000000000000000000",
        "contact_bic": "123",
        "card_account_attributes": {
            "account_number": 1234567890,
            "holder_name": "John Doe",
            "network": "VISA"
        },
        "reminder_for_payment": True,
        "payment_reminder_days": 15,
        "terms": "1m1",
        "extra_info": "Some extra info",
        "legal_literals": "Legal literals",
        "delivery_party_name": "Delivery party name",
        "delivery_location_id": 83745498753497,
        "delivery_location_type": 88,
        "delivery_date": "2024-07-07",
        "delivery_address": "Invented address, 1",
        "delivery_address2": "Invented address, 2",
        "delivery_postalcode": "80808",
        "delivery_city": "Barcelona",
        "delivery_province": "Barcelona",
        "delivery_country": "ES",
        "invoice_lines_attributes": [
            {
                "position": 1,
                "quantity": 1,
                "price": 10,
                "description": "Item 1",
                "extension_amount": 10,
                "unit": 1,
                "discount_amount": 100,
                "discount_percent": 20,
                "discount_text": "Discount",
                "charge_amount": 4,
                "charge_percent": 20,
                "charge_reason": "Charge",
                "taxes_attributes": [
                    {
                        "name": "IVA",
                        "category": "S",
                        "percent": 21,
                        "comment": "IVA 21%"
                    }
                ],
                "article_code": "9873242",
                "article_code2": "10986700",
                "article_code2_scheme": "0160",
                "article_code_buyer": "9873242",
                "classification_code": "9873242",
                "classification_code_scheme": "0160",
                "item_origin_country": "es",
                "buyer_accounting_reference": "1287:65464",
                "delivery_note_date": "2024-09-12",
                "delivery_note_number": "123",
                "file_reference": "BE-123",
                "file_date": "2024-09-12",
                "invoicing_period_start": "2017-10-10",
                "invoicing_period_end": "2017-10-15",
                "issuer_transaction_reference": "123",
                "issuer_transaction_date": "2024-09-12",
                "notes": "string",
                "notes2": "Long description of the item on the invoice line",
                "ponumber": "PO123",
                "receiver_transaction_date": "2024-09-12",
                "receiver_contract_reference": "reference_123",
                "receiver_contract_date": "2024-09-12",
                "sequence_number": "3",
                "contact_reference": "3",
                "receipt_reference": {
                    "identifier": "123456",
                    "number": 123,
                    "date": "2024-09-12"
                },
                "additional_item_properties_attributes": [
                    {
                        "name": "string",
                        "value": "string"
                    }
                ]
            }
        ],
        "payment_dues_attributes": [
            {
                "due_date": "2024-09-12",
                "amount": 10
            }
        ],
        "type_document": "TD01",
        "tax_report_description": "Tax report for Invoice 1",
        "apply_taxes_to_charge": False,
        "charge_is_reimbursable_expense": False,
        "client_email_override": "john_doe@example.net, jane_doe@example.net",
        "company_email_override": "john_doe_override@example.net",
        "receiver_contract_reference": "123",
        "dire": "ES12345678",
        "fa_address": "Invented address, 1",
        "fa_bank_code": "ES6000000000000000000000",
        "fa_bic": "123",
        "fa_clauses": "Clauses",
        "fa_country": "ES",
        "fa_duedate": "2024-09-12",
        "fa_iban": "ES6000000000000000000000",
        "fa_import": 100,
        "fa_info": "Information",
        "fa_name": "Name",
        "fa_payment_method": "2",
        "fa_person_type": "J",
        "fa_postcode": "80808",
        "fa_province": "Barcelona",
        "fa_residence_type": "string",
        "fa_taxcode": "ES12345678",
        "fa_town": "Barcelona",
        "accounting_unit": "ES00000000",
        "managing_unit": "ES00000000",
        "proponent_unit": "ES00000000",
        "special_regime_key": "01",
        "special_regime_key_additional": "01",
        "contract_unit": "Contracting Unit",
        "processing_unit": "Processing Unit",
        "amend_code_tax": "R1",
        "type_operation": "services"
    }
}
headers = {
    "content-type": "application/json",
    "X-B2B-API-Key": "db89fe23af56f6e8f1d8f8b6ce321d97a6a06a60"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)

<?xml version="1.0" encoding="UTF-8"?><errors type="array"><error>Validation failed: Iban is invalid</error></errors>


Send Invoice :


import requests

url = "https://app-staging.b2brouter.net/invoices/send_invoice/id.xml"

headers = {
    "accept": "application/xml",
    "X-B2B-API-Key": "db89fe23af56f6e8f1d8f8b6ce321d97a6a06a60"
}

response = requests.post(url, headers=headers)

print(response.text)