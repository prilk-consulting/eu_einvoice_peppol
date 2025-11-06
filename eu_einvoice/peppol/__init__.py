# Copyright (c) 2025, Prilk Consulting BV and contributors
"""
PEPPOL Module

This module provides PEPPOL BIS Billing 3.0 compliant UBL 2.1 XML generation,
validation, and parsing functionality.
"""

# UBL 2.1 standard namespaces (shared constant)
UBL_NAMESPACES = {
    'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
}

# PEPPOL BIS Billing 3.0 Constants
PEPPOL_CUSTOMIZATION_ID = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
PEPPOL_PROFILE_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

# Global code retrievers for PEPPOL standardized codes (shared across generator and import)
from eu_einvoice.common_codes import CommonCodeRetriever

duty_tax_fee_category_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNCL5305"], "S")
uom_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNECERec20"], "C62")
payment_means_codes = CommonCodeRetriever(["urn:peppol:id:codelist:UNCL4461"], "ZZZ")
country_codes = CommonCodeRetriever(["urn:peppol:id:codelist:ISO3166-1_Alpha2"], "DE")
currency_codes = CommonCodeRetriever(["urn:peppol:id:codelist:ISO4217"], "EUR")
electronic_address_schemes = CommonCodeRetriever(["urn:peppol:id:codelist:eas"], "EM")
