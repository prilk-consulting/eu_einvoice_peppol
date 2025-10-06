"""
PEPPOL Utilities

This module provides utility classes and functions for PEPPOL BIS Billing 3.0
implementation, including code list management and validation results.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationMessage:
    """A validation message from PEPPOL validation."""
    
    rule_id: str
    severity: ValidationSeverity
    message: str
    context: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    test_expression: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of PEPPOL validation."""
    
    is_valid: bool
    errors: List[ValidationMessage] = field(default_factory=list)
    warnings: List[ValidationMessage] = field(default_factory=list)
    info_messages: List[ValidationMessage] = field(default_factory=list)
    profile_used: Optional[str] = None
    validation_time: Optional[float] = None
    total_rules_checked: int = 0
    
    def add_error(self, rule_id: str, message: str, **kwargs):
        """Add an error message."""
        self.errors.append(ValidationMessage(
            rule_id=rule_id,
            severity=ValidationSeverity.ERROR,
            message=message,
            **kwargs
        ))
        self.is_valid = False
    
    def add_warning(self, rule_id: str, message: str, **kwargs):
        """Add a warning message."""
        self.warnings.append(ValidationMessage(
            rule_id=rule_id,
            severity=ValidationSeverity.WARNING,
            message=message,
            **kwargs
        ))
    
    def add_info(self, rule_id: str, message: str, **kwargs):
        """Add an info message."""
        self.info_messages.append(ValidationMessage(
            rule_id=rule_id,
            severity=ValidationSeverity.INFO,
            message=message,
            **kwargs
        ))
    
    def get_all_messages(self) -> List[ValidationMessage]:
        """Get all validation messages."""
        return self.errors + self.warnings + self.info_messages
    
    def get_message_count(self) -> Dict[str, int]:
        """Get count of messages by severity."""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info_messages),
            "total": len(self.get_all_messages())
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "profile_used": self.profile_used,
            "validation_time": self.validation_time,
            "total_rules_checked": self.total_rules_checked,
            "message_count": self.get_message_count(),
            "errors": [
                {
                    "rule_id": msg.rule_id,
                    "message": msg.message,
                    "context": msg.context,
                    "line_number": msg.line_number,
                    "column_number": msg.column_number,
                    "test_expression": msg.test_expression,
                    "details": msg.details
                }
                for msg in self.errors
            ],
            "warnings": [
                {
                    "rule_id": msg.rule_id,
                    "message": msg.message,
                    "context": msg.context,
                    "line_number": msg.line_number,
                    "column_number": msg.column_number,
                    "test_expression": msg.test_expression,
                    "details": msg.details
                }
                for msg in self.warnings
            ],
            "info_messages": [
                {
                    "rule_id": msg.rule_id,
                    "message": msg.message,
                    "context": msg.context,
                    "line_number": msg.line_number,
                    "column_number": msg.column_number,
                    "test_expression": msg.test_expression,
                    "details": msg.details
                }
                for msg in self.info_messages
            ]
        }


class CodeListManager:
    """Manages PEPPOL code lists from the official repository."""
    
    def __init__(self, code_lists_dir: Optional[Path] = None):
        if code_lists_dir is None:
            # Default to the official repository structure
            current_dir = Path(__file__).parent
            self.code_lists_dir = current_dir.parent.parent / "peppol-bis-invoice-3" / "structure" / "codelist"
        else:
            self.code_lists_dir = code_lists_dir
        
        self._code_lists: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._loaded_files: set = set()
    
    def load_code_list(self, filename: str) -> bool:
        """Load a code list from XML file."""
        file_path = self.code_lists_dir / filename
        
        if not file_path.exists():
            return False
        
        if filename in self._loaded_files:
            return True
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract code list ID from filename
            code_list_id = filename.replace('.xml', '')
            
            # Parse code list structure
            codes = {}
            
            # Handle different code list formats
            if root.tag.endswith('CodeList'):
                # Standard code list format
                for code_elem in root.findall('.//Code'):
                    code_id = code_elem.get('ID', '')
                    if code_id:
                        codes[code_id] = {}
                        for name_elem in code_elem.findall('.//Name'):
                            lang = name_elem.get('languageID', 'en')
                            codes[code_id][lang] = name_elem.text or ''
            
            elif root.tag.endswith('codelist'):
                # Alternative format
                for code_elem in root.findall('.//c'):
                    code_id = code_elem.get('id', '')
                    if code_id:
                        codes[code_id] = {}
                        for text_elem in code_elem.findall('.//t'):
                            lang = text_elem.get('id', 'en')
                            codes[code_id][lang] = text_elem.text or ''
            
            self._code_lists[code_list_id] = codes
            self._loaded_files.add(filename)
            return True
            
        except Exception as e:
            print(f"Error loading code list {filename}: {e}")
            return False
    
    def get_code_description(self, code_list_id: str, code: str, language: str = 'en') -> Optional[str]:
        """Get description for a code in a specific language."""
        if code_list_id not in self._code_lists:
            # Try to load the code list
            filename = f"{code_list_id}.xml"
            if not self.load_code_list(filename):
                return None
        
        code_list = self._code_lists.get(code_list_id, {})
        code_info = code_list.get(code, {})
        
        # Try requested language first, then fallback to English
        return code_info.get(language) or code_info.get('en')
    
    def is_valid_code(self, code_list_id: str, code: str) -> bool:
        """Check if a code is valid in the given code list."""
        if code_list_id not in self._code_lists:
            # Try to load the code list
            filename = f"{code_list_id}.xml"
            if not self.load_code_list(filename):
                return False
        
        return code in self._code_lists.get(code_list_id, {})
    
    def get_available_codes(self, code_list_id: str) -> List[str]:
        """Get all available codes in a code list."""
        if code_list_id not in self._code_lists:
            # Try to load the code list
            filename = f"{code_list_id}.xml"
            if not self.load_code_list(filename):
                return []
        
        return list(self._code_lists.get(code_list_id, {}).keys())
    
    def get_code_list_info(self, code_list_id: str) -> Dict[str, Any]:
        """Get information about a code list."""
        if code_list_id not in self._code_lists:
            # Try to load the code list
            filename = f"{code_list_id}.xml"
            if not self.load_code_list(filename):
                return {"error": f"Code list {code_list_id} not found"}
        
        codes = self._code_lists.get(code_list_id, {})
        return {
            "id": code_list_id,
            "filename": f"{code_list_id}.xml",
            "code_count": len(codes),
            "available_codes": list(codes.keys()),
            "languages": list(set(
                lang for code_info in codes.values() 
                for lang in code_info.keys()
            ))
        }
    
    def load_all_code_lists(self) -> Dict[str, bool]:
        """Load all available code lists."""
        results = {}
        
        if not self.code_lists_dir.exists():
            return results
        
        for xml_file in self.code_lists_dir.glob("*.xml"):
            filename = xml_file.name
            code_list_id = filename.replace('.xml', '')
            results[code_list_id] = self.load_code_list(filename)
        
        return results
    
    def get_loaded_code_lists(self) -> List[str]:
        """Get list of loaded code lists."""
        return list(self._code_lists.keys())
    
    def validate_ubl_document(self, ubl_content: str) -> ValidationResult:
        """Validate UBL document against code lists."""
        result = ValidationResult(is_valid=True)
        
        try:
            root = ET.fromstring(ubl_content)
            
            # Validate document type codes
            self._validate_document_type_codes(root, result)
            
            # Validate payment means codes
            self._validate_payment_means_codes(root, result)
            
            # Validate tax category codes
            self._validate_tax_category_codes(root, result)
            
            # Validate currency codes
            self._validate_currency_codes(root, result)
            
            # Validate country codes
            self._validate_country_codes(root, result)
            
            # Validate unit codes
            self._validate_unit_codes(root, result)
            
        except ET.ParseError as e:
            result.add_error("XML_PARSE", f"Invalid XML: {e}")
        
        return result
    
    def _validate_document_type_codes(self, root: ET.Element, result: ValidationResult):
        """Validate document type codes."""
        for elem in root.findall('.//cbc:InvoiceTypeCode'):
            code = elem.text
            if code and not self.is_valid_code('UNCL1001-inv', code):
                result.add_error(
                    "INVALID_DOCUMENT_TYPE",
                    f"Invalid invoice type code: {code}",
                    context=elem.tag,
                    test_expression=f"cbc:InvoiceTypeCode = '{code}'"
                )
    
    def _validate_payment_means_codes(self, root: ET.Element, result: ValidationResult):
        """Validate payment means codes."""
        for elem in root.findall('.//cbc:PaymentMeansCode'):
            code = elem.text
            if code and not self.is_valid_code('UNCL4461', code):
                result.add_error(
                    "INVALID_PAYMENT_MEANS",
                    f"Invalid payment means code: {code}",
                    context=elem.tag,
                    test_expression=f"cbc:PaymentMeansCode = '{code}'"
                )
    
    def _validate_tax_category_codes(self, root: ET.Element, result: ValidationResult):
        """Validate tax category codes."""
        for elem in root.findall('.//cac:TaxCategory/cbc:ID'):
            code = elem.text
            if code and not self.is_valid_code('UNCL5305', code):
                result.add_error(
                    "INVALID_TAX_CATEGORY",
                    f"Invalid tax category code: {code}",
                    context=elem.tag,
                    test_expression=f"cac:TaxCategory/cbc:ID = '{code}'"
                )
    
    def _validate_currency_codes(self, root: ET.Element, result: ValidationResult):
        """Validate currency codes."""
        for elem in root.findall('.//cbc:DocumentCurrencyCode'):
            code = elem.text
            if code and not self.is_valid_code('ISO4217_2015', code):
                result.add_error(
                    "INVALID_CURRENCY",
                    f"Invalid currency code: {code}",
                    context=elem.tag,
                    test_expression=f"cbc:DocumentCurrencyCode = '{code}'"
                )
    
    def _validate_country_codes(self, root: ET.Element, result: ValidationResult):
        """Validate country codes."""
        for elem in root.findall('.//cac:Country/cbc:IdentificationCode'):
            code = elem.text
            if code and not self.is_valid_code('ISO3166-1_Alpha2', code):
                result.add_error(
                    "INVALID_COUNTRY",
                    f"Invalid country code: {code}",
                    context=elem.tag,
                    test_expression=f"cac:Country/cbc:IdentificationCode = '{code}'"
                )
    
    def _validate_unit_codes(self, root: ET.Element, result: ValidationResult):
        """Validate unit of measure codes."""
        for elem in root.findall('.//cbc:InvoicedQuantity'):
            unit_code = elem.get('unitCode')
            if unit_code and not self.is_valid_code('UNECERec20-11e', unit_code):
                result.add_error(
                    "INVALID_UNIT",
                    f"Invalid unit of measure code: {unit_code}",
                    context=elem.tag,
                    test_expression=f"cbc:InvoicedQuantity[@unitCode='{unit_code}']"
                )


# Global code list manager instance
code_list_manager = CodeListManager()


def get_code_description(code_list_id: str, code: str, language: str = 'en') -> Optional[str]:
    """Get description for a code in a specific language."""
    return code_list_manager.get_code_description(code_list_id, code, language)


def is_valid_code(code_list_id: str, code: str) -> bool:
    """Check if a code is valid in the given code list."""
    return code_list_manager.is_valid_code(code_list_id, code)


def validate_ubl_document(ubl_content: str) -> ValidationResult:
    """Validate UBL document against code lists."""
    return code_list_manager.validate_ubl_document(ubl_content) 