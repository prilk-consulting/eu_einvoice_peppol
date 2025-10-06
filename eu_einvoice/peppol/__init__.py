"""
PEPPOL BIS Billing 3.0 Implementation

This package provides a complete implementation of PEPPOL BIS Billing 3.0
for ERPNext, including UBL 2.1 XML generation, validation, and code list management.
"""

from .profiles import PEPPOLProfile, get_profile_info, get_available_profiles
from .utils import ValidationResult, ValidationMessage, ValidationSeverity
from .generator import PEPPOLGenerator
from .validator import PEPPOLValidator
from .codelist import CodeListManager, code_list_manager
from .core import PEPPOLGenerator, PEPPOLValidator

__version__ = "3.0.0"
__author__ = "ERPNext Team"

# Main classes for easy import
__all__ = [
    'PEPPOLProfile',
    'PEPPOLGenerator',
    'PEPPOLValidator', 
    "CodeListManager",
    'ValidationResult',
    'ValidationMessage',
    'ValidationSeverity',
    'get_profile_info',
    'get_available_profiles',
    'code_list_manager'
] 