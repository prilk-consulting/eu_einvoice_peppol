"""
PEPPOL Code Lists

This module provides code list management for PEPPOL BIS Billing 3.0,
loading and validating official code lists from the PEPPOL repository.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass


@dataclass
class CodeListInfo:
    """Information about a code list."""
    
    id: str
    name: str
    description: str
    version: str
    agency: str
    codes_count: int
    file_path: str


class CodeListManager:
    """Manages PEPPOL code lists from the official repository."""
    
    def __init__(self, code_lists_dir: Optional[Path] = None):
        if code_lists_dir is None:
            # Default to the official repository structure
            current_dir = Path(__file__).parent
            self.code_lists_dir = current_dir / "peppol-bis-invoice-3" / "structure" / "codelist"
        else:
            self.code_lists_dir = code_lists_dir
        
        self._code_lists: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._loaded_files: set = set()
        self._code_list_info: Dict[str, CodeListInfo] = {}
    
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
            
            # Store code list info
            self._code_list_info[code_list_id] = CodeListInfo(
                id=code_list_id,
                name=code_list_id.replace('_', ' ').title(),
                description=f"PEPPOL {code_list_id} code list",
                version="3.0",
                agency="OpenPEPPOL",
                codes_count=len(codes),
                file_path=str(file_path)
            )
            
            return True
            
        except Exception as e:
            print(f"Error loading code list {filename}: {e}")
            return False
    
    def get_code_description(self, code_list_id: str, code: str, language: str = 'en') -> Optional[str]:
        """Get description for a specific code in a code list."""
        
        if code_list_id not in self._code_lists:
            # Try to load the code list
            if not self.load_code_list(f"{code_list_id}.xml"):
                return None
        
        code_list = self._code_lists.get(code_list_id, {})
        code_info = code_list.get(code, {})
        
        # Try requested language first, then fallback to English
        description = code_info.get(language) or code_info.get('en')
        return description
    
    def is_valid_code(self, code_list_id: str, code: str) -> bool:
        """Check if a code is valid in a specific code list."""
        
        if code_list_id not in self._code_lists:
            # Try to load the code list
            if not self.load_code_list(f"{code_list_id}.xml"):
                return False
        
        return code in self._code_lists.get(code_list_id, {})
    
    def get_available_codes(self, code_list_id: str) -> List[str]:
        """Get all available codes in a code list."""
        
        if code_list_id not in self._code_lists:
            # Try to load the code list
            if not self.load_code_list(f"{code_list_id}.xml"):
                return []
        
        return list(self._code_lists.get(code_list_id, {}).keys())
    
    def get_code_list_info(self, code_list_id: str) -> Dict[str, Any]:
        """Get information about a code list."""
        
        if code_list_id not in self._code_list_info:
            # Try to load the code list
            if not self.load_code_list(f"{code_list_id}.xml"):
                return {}
        
        info = self._code_list_info.get(code_list_id)
        if info:
            return {
                "id": info.id,
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "agency": info.agency,
                "codes_count": info.codes_count,
                "file_path": info.file_path,
                "loaded": code_list_id in self._loaded_files
            }
        
        return {}
    
    def load_all_code_lists(self) -> Dict[str, bool]:
        """Load all available code lists."""
        
        results = {}
        
        if not self.code_lists_dir.exists():
            return results
        
        for xml_file in self.code_lists_dir.glob("*.xml"):
            filename = xml_file.name
            results[filename] = self.load_code_list(filename)
        
        return results
    
    def get_loaded_code_lists(self) -> List[str]:
        """Get list of loaded code lists."""
        return list(self._loaded_files)
    
    def validate_ubl_document(self, ubl_content: str) -> Dict[str, List[str]]:
        """Validate UBL document against code lists."""
        
        from .utils import ValidationResult
        
        result = ValidationResult(is_valid=True)
        
        try:
            root = ET.fromstring(ubl_content)
            
            # Validate different code list types
            self._validate_document_type_codes(root, result)
            self._validate_payment_means_codes(root, result)
            self._validate_tax_category_codes(root, result)
            self._validate_currency_codes(root, result)
            self._validate_country_codes(root, result)
            self._validate_unit_codes(root, result)
            
            return {
                "errors": [e.message for e in result.errors],
                "warnings": [w.message for w in result.warnings]
            }
            
        except ET.ParseError:
            return {"errors": ["Invalid XML content"], "warnings": []}
    
    def _validate_document_type_codes(self, root: ET.Element, result):
        """Validate document type codes."""
        
        doc_type_codes = root.findall('.//cbc:InvoiceTypeCode', 
                                     namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        
        for code_elem in doc_type_codes:
            code = code_elem.text
            if code and not self.is_valid_code('DocumentTypeCode', code):
                result.add_error("CODE_LIST_ERROR", f"Invalid document type code: {code}")
    
    def _validate_payment_means_codes(self, root: ET.Element, result):
        """Validate payment means codes."""
        
        payment_codes = root.findall('.//cbc:PaymentMeansCode', 
                                    namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        
        for code_elem in payment_codes:
            code = code_elem.text
            if code and not self.is_valid_code('PaymentMeansCode', code):
                result.add_error("CODE_LIST_ERROR", f"Invalid payment means code: {code}")
    
    def _validate_tax_category_codes(self, root: ET.Element, result):
        """Validate tax category codes."""
        
        tax_codes = root.findall('.//cac:TaxCategory//cbc:ID', 
                                namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                          'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        
        for code_elem in tax_codes:
            code = code_elem.text
            if code and not self.is_valid_code('TaxCategoryCode', code):
                result.add_error("CODE_LIST_ERROR", f"Invalid tax category code: {code}")
    
    def _validate_currency_codes(self, root: ET.Element, result):
        """Validate currency codes."""
        
        currency_codes = root.findall('.//cbc:DocumentCurrencyCode', 
                                     namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        
        for code_elem in currency_codes:
            code = code_elem.text
            if code and not self.is_valid_code('CurrencyCode', code):
                result.add_error("CODE_LIST_ERROR", f"Invalid currency code: {code}")
    
    def _validate_country_codes(self, root: ET.Element, result):
        """Validate country codes."""
        
        country_codes = root.findall('.//cac:Country//cbc:IdentificationCode', 
                                    namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                                              'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        
        for code_elem in country_codes:
            code = code_elem.text
            if code and not self.is_valid_code('CountryCode', code):
                result.add_error("CODE_LIST_ERROR", f"Invalid country code: {code}")
    
    def _validate_unit_codes(self, root: ET.Element, result):
        """Validate unit codes."""
        
        unit_codes = root.findall('.//cbc:InvoicedQuantity', 
                                 namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
        
        for code_elem in unit_codes:
            code = code_elem.get('unitCode')
            if code and not self.is_valid_code('UnitCode', code):
                result.add_error("CODE_LIST_ERROR", f"Invalid unit code: {code}")
    
    def get_code_list_summary(self) -> Dict[str, Any]:
        """Get summary of all code lists."""
        
        summary = {
            "total_loaded": len(self._loaded_files),
            "code_lists": {}
        }
        
        for code_list_id, info in self._code_list_info.items():
            summary["code_lists"][code_list_id] = {
                "name": info.name,
                "codes_count": info.codes_count,
                "loaded": code_list_id in self._loaded_files
            }
        
        return summary
    
    def export_code_list(self, code_list_id: str, format: str = 'json') -> Optional[str]:
        """Export a code list in specified format."""
        
        if code_list_id not in self._code_lists:
            if not self.load_code_list(f"{code_list_id}.xml"):
                return None
        
        codes = self._code_lists.get(code_list_id, {})
        
        if format.lower() == 'json':
            import json
            return json.dumps(codes, indent=2)
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Code', 'Description (EN)', 'Description (NL)', 'Description (DE)'])
            
            for code, descriptions in codes.items():
                writer.writerow([
                    code,
                    descriptions.get('en', ''),
                    descriptions.get('nl', ''),
                    descriptions.get('de', '')
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global code list manager instance
code_list_manager = CodeListManager()


# Convenience functions
def get_code_description(code_list_id: str, code: str, language: str = 'en') -> Optional[str]:
    """Get description for a specific code in a code list."""
    return code_list_manager.get_code_description(code_list_id, code, language)


def is_valid_code(code_list_id: str, code: str) -> bool:
    """Check if a code is valid in a specific code list."""
    return code_list_manager.is_valid_code(code_list_id, code)


def validate_ubl_document(ubl_content: str) -> Dict[str, List[str]]:
    """Validate UBL document against code lists."""
    return code_list_manager.validate_ubl_document(ubl_content) 