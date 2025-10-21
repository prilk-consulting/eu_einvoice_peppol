"""
PEPPOL Profile Definitions

This module defines the PEPPOL BIS Billing 3.0 profiles and their essential
characteristics for XML generation and validation.
"""

from enum import Enum
from typing import Dict


class PEPPOLProfile(Enum):
    """PEPPOL BIS Billing 3.0 profiles."""

    # Core PEPPOL profile (currently the only one implemented)
    PEPPOL_BIS_30 = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
    

# Profile information mapping (only contains what's actually used)
PEPPOL_PROFILE_INFO: Dict[str, Dict[str, str]] = {
    "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0": {
        "customization_id": "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
        "name": "PEPPOL BIS Billing 3.0",
        "description": "Core PEPPOL BIS Billing 3.0 specification"
    }
}


def get_profile_info(profile: PEPPOLProfile) -> Dict[str, str]:
    """
    Get essential profile information.

    Currently only returns customization_id which is needed for XML generation.
    All other profile metadata (schematron files, code lists, etc.) is handled
    directly in the validator since country-specific rules are implemented
    conditionally in the main schematron file.
    """
    return PEPPOL_PROFILE_INFO.get(profile.value, {})


def get_available_profiles() -> list[PEPPOLProfile]:
    """Get list of available profiles."""
    return list(PEPPOLProfile) 