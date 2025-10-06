"""
PEPPOL Profile Definitions

This module defines the PEPPOL BIS Billing 3.0 profiles and their characteristics
based on the official OpenPEPPOL specifications.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class PEPPOLProfile(Enum):
    """PEPPOL BIS Billing 3.0 profiles."""
    
    # Core PEPPOL profiles
    PEPPOL_BIS_30 = "urn:fdc:peppol.eu:2017:poacc:billing:3.0"
    
    # Country-specific profiles (CIUS)
    PEPPOL_BIS_30_NL = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:nl"
    PEPPOL_BIS_30_BE = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:be"
    PEPPOL_BIS_30_DE = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:de"
    PEPPOL_BIS_30_FR = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:fr"
    PEPPOL_BIS_30_IT = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:it"
    PEPPOL_BIS_30_ES = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:es"
    PEPPOL_BIS_30_SE = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:se"
    PEPPOL_BIS_30_NO = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:no"
    PEPPOL_BIS_30_DK = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:dk"
    PEPPOL_BIS_30_FI = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:fi"
    PEPPOL_BIS_30_PT = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:pt"
    PEPPOL_BIS_30_PL = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:pl"
    PEPPOL_BIS_30_CZ = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:cz"
    PEPPOL_BIS_30_AT = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:at"
    PEPPOL_BIS_30_CH = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:ch"
    PEPPOL_BIS_30_IE = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:ie"
    PEPPOL_BIS_30_GR = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:gr"
    PEPPOL_BIS_30_HU = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:hu"
    PEPPOL_BIS_30_RO = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:ro"
    PEPPOL_BIS_30_BG = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:bg"
    PEPPOL_BIS_30_HR = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:hr"
    PEPPOL_BIS_30_SI = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:si"
    PEPPOL_BIS_30_SK = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:sk"
    PEPPOL_BIS_30_LT = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:lt"
    PEPPOL_BIS_30_LV = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:lv"
    PEPPOL_BIS_30_EE = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:ee"
    PEPPOL_BIS_30_CY = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:cy"
    PEPPOL_BIS_30_MT = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:mt"
    PEPPOL_BIS_30_LU = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:lu"
    PEPPOL_BIS_30_IS = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:is"
    PEPPOL_BIS_30_LI = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:li"
    PEPPOL_BIS_30_MC = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:mc"
    PEPPOL_BIS_30_SM = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:sm"
    PEPPOL_BIS_30_VA = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:va"
    PEPPOL_BIS_30_AD = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:ad"
    PEPPOL_BIS_30_AL = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:al"
    PEPPOL_BIS_30_BA = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:ba"
    PEPPOL_BIS_30_ME = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:me"
    PEPPOL_BIS_30_MK = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:mk"
    PEPPOL_BIS_30_RS = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:rs"
    PEPPOL_BIS_30_TR = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:tr"
    PEPPOL_BIS_30_UA = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:ua"
    PEPPOL_BIS_30_GB = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:gb"
    PEPPOL_BIS_30_XK = "urn:fdc:peppol.eu:2017:poacc:billing:3.0:xk"


@dataclass
class ProfileInfo:
    """Information about a PEPPOL profile."""
    
    name: str
    description: str
    country_code: str
    customization_id: str
    schematron_file: str
    xslt_file: str
    code_lists: List[str]
    business_rules: List[str]
    is_cius: bool = False
    parent_profile: Optional[PEPPOLProfile] = None


class ProfileRegistry:
    """Registry for PEPPOL profiles and their configurations."""
    
    def __init__(self):
        self._profiles: Dict[PEPPOLProfile, ProfileInfo] = {}
        self._initialize_profiles()
    
    def _initialize_profiles(self):
        """Initialize the profile registry with official PEPPOL profiles."""
        
        # Base PEPPOL BIS 3.0 profile
        self._profiles[PEPPOLProfile.PEPPOL_BIS_30] = ProfileInfo(
            name="PEPPOL BIS Billing 3.0",
            description="Core PEPPOL BIS Billing 3.0 specification",
            country_code="EU",
            customization_id="urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
            schematron_file="PEPPOL-EN16931-UBL.sch",
            xslt_file="stylesheet-ubl.xslt",
            code_lists=[
                "UNCL1001-inv.xml",      # Document type codes
                "UNCL4461.xml",          # Payment means codes
                "UNCL5305.xml",          # Duty/tax/fee category codes
                "UNCL7143.xml",          # Item type identification codes
                "UNCL7161.xml",          # Adjustment reason codes
                "UNCL5189.xml",          # Charge reason codes
                "UNCL2005.xml",          # Currency codes
                "UNCL1153.xml",          # Text subject codes
                "UNECERec20-11e.xml",    # Unit of measure codes
                "ISO3166-1_Alpha2.xml",  # Country codes
                "ISO4217_2015.xml",      # Currency codes
                "VATEX.xml",             # VAT exemption reason codes
                "eas.xml",               # Electronic address scheme codes
                "icd.xml",               # Identity code scheme codes
                "SEPA.xml",              # SEPA codes
                "MimeCode.xml",          # MIME type codes
            ],
            business_rules=[
                "BR-01", "BR-02", "BR-03", "BR-04", "BR-05", "BR-06", "BR-07", "BR-08", "BR-09", "BR-10",
                "BR-11", "BR-12", "BR-13", "BR-14", "BR-15", "BR-16", "BR-17", "BR-18", "BR-19", "BR-20",
                "BR-21", "BR-22", "BR-23", "BR-24", "BR-25", "BR-26", "BR-27", "BR-28", "BR-29", "BR-30",
                "BR-31", "BR-32", "BR-33", "BR-34", "BR-35", "BR-36", "BR-37", "BR-38", "BR-39", "BR-40",
                "BR-41", "BR-42", "BR-43", "BR-44", "BR-45", "BR-46", "BR-47", "BR-48", "BR-49", "BR-50",
                "BR-51", "BR-52", "BR-53", "BR-54", "BR-55", "BR-56", "BR-57", "BR-58", "BR-59", "BR-60",
                "BR-61", "BR-62", "BR-63", "BR-64", "BR-65", "BR-66", "BR-67"
            ],
            is_cius=False
        )
        
        # Country-specific CIUS profiles
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_NL, "Netherlands", "NL")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_BE, "Belgium", "BE")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_DE, "Germany", "DE")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_FR, "France", "FR")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_IT, "Italy", "IT")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_ES, "Spain", "ES")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_SE, "Sweden", "SE")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_NO, "Norway", "NO")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_DK, "Denmark", "DK")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_FI, "Finland", "FI")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_PT, "Portugal", "PT")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_PL, "Poland", "PL")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_CZ, "Czech Republic", "CZ")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_AT, "Austria", "AT")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_CH, "Switzerland", "CH")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_IE, "Ireland", "IE")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_GR, "Greece", "GR")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_HU, "Hungary", "HU")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_RO, "Romania", "RO")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_BG, "Bulgaria", "BG")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_HR, "Croatia", "HR")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_SI, "Slovenia", "SI")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_SK, "Slovakia", "SK")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_LT, "Lithuania", "LT")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_LV, "Latvia", "LV")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_EE, "Estonia", "EE")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_CY, "Cyprus", "CY")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_MT, "Malta", "MT")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_LU, "Luxembourg", "LU")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_IS, "Iceland", "IS")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_LI, "Liechtenstein", "LI")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_MC, "Monaco", "MC")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_SM, "San Marino", "SM")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_VA, "Vatican City", "VA")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_AD, "Andorra", "AD")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_AL, "Albania", "AL")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_BA, "Bosnia and Herzegovina", "BA")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_ME, "Montenegro", "ME")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_MK, "North Macedonia", "MK")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_RS, "Serbia", "RS")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_TR, "Turkey", "TR")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_UA, "Ukraine", "UA")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_GB, "United Kingdom", "GB")
        self._add_cius_profile(PEPPOLProfile.PEPPOL_BIS_30_XK, "Kosovo", "XK")
    
    def _add_cius_profile(self, profile: PEPPOLProfile, country_name: str, country_code: str):
        """Add a country-specific CIUS profile."""
        base_profile = self._profiles[PEPPOLProfile.PEPPOL_BIS_30]
        
        self._profiles[profile] = ProfileInfo(
            name=f"PEPPOL BIS Billing 3.0 - {country_name}",
            description=f"PEPPOL BIS Billing 3.0 with {country_name} CIUS extensions",
            country_code=country_code,
            customization_id=f"urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0:{country_code.lower()}",
            schematron_file=f"PEPPOL-EN16931-UBL-{country_code.upper()}.sch",
            xslt_file="stylesheet-ubl.xslt",
            code_lists=base_profile.code_lists.copy(),
            business_rules=base_profile.business_rules.copy(),
            is_cius=True,
            parent_profile=PEPPOLProfile.PEPPOL_BIS_30
        )
    
    def get_profile(self, profile: PEPPOLProfile) -> ProfileInfo:
        """Get profile information."""
        return self._profiles.get(profile)
    
    def get_profile_by_country(self, country_code: str) -> Optional[PEPPOLProfile]:
        """Get profile by country code."""
        for profile, info in self._profiles.items():
            if info.country_code == country_code.upper():
                return profile
        return None
    
    def get_available_profiles(self) -> List[PEPPOLProfile]:
        """Get list of available profiles."""
        return list(self._profiles.keys())
    
    def get_cius_profiles(self) -> List[PEPPOLProfile]:
        """Get list of CIUS profiles."""
        return [profile for profile, info in self._profiles.items() if info.is_cius]
    
    def get_base_profiles(self) -> List[PEPPOLProfile]:
        """Get list of base profiles (non-CIUS)."""
        return [profile for profile, info in self._profiles.items() if not info.is_cius]


# Global profile registry instance
profile_registry = ProfileRegistry()


def get_profile_info(profile: PEPPOLProfile) -> ProfileInfo:
    """Get profile information."""
    return profile_registry.get_profile(profile)


def get_profile_by_country(country_code: str) -> Optional[PEPPOLProfile]:
    """Get profile by country code."""
    return profile_registry.get_profile_by_country(country_code)


def get_available_profiles() -> List[PEPPOLProfile]:
    """Get list of available profiles."""
    return profile_registry.get_available_profiles() 