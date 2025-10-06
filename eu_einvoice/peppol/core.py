"""
PEPPOL Core Implementation

This module provides the core PEPPOL BIS Billing 3.0 functionality including
UBL 2.1 XML generation and validation using official Schematron rules.

This module serves as a convenience import point, re-exporting the main classes
from their respective modules.
"""

# Import the main classes from their dedicated modules
from .generator import PEPPOLGenerator
from .validator import PEPPOLValidator

# Re-export for convenience
__all__ = ['PEPPOLGenerator', 'PEPPOLValidator'] 