from enum import Enum
from functools import total_ordering


@total_ordering
class EInvoiceProfile(Enum):
	"""
	Profiles according to Factur-X Specification 1.07.2 page 18.
	'MINIMUM' and 'BASIC WL' are not included because they are not valid tax invoices.
	"""

	BASIC = "BASIC"
	EN16931 = "EN 16931"
	EXTENDED = "EXTENDED"
	XRECHNUNG = "XRECHNUNG"
	PEPPOL = "PEPPOL"

	def __lt__(self, other):
		# https://stackoverflow.com/a/39269589
		order = [
			EInvoiceProfile.BASIC,
			EInvoiceProfile.EN16931,
			EInvoiceProfile.XRECHNUNG,
			EInvoiceProfile.EXTENDED,
			EInvoiceProfile.PEPPOL,
		]
		return order.index(self) < order.index(other)


# Map of EInvoiceProfile to drafthorse schema name or XSD Schema name
PROFILE_TO_SCHEMA = {
	EInvoiceProfile.BASIC: "FACTUR-X_BASIC",
	EInvoiceProfile.EN16931: "FACTUR-X_EN16931",
	EInvoiceProfile.XRECHNUNG: "FACTUR-X_EN16931",
	EInvoiceProfile.EXTENDED: "FACTUR-X_EXTENDED",
}

# Map of EInvoiceProfile to GuidelineSpecifiedDocumentContextParameter
PROFILE_TO_GUIDELINE = {
	EInvoiceProfile.BASIC: "urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic",
	EInvoiceProfile.EN16931: "urn:cen.eu:en16931:2017",
	EInvoiceProfile.XRECHNUNG: "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0",
	EInvoiceProfile.EXTENDED: "urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:extended",
	EInvoiceProfile.PEPPOL: "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",  # PEPPOL BIS 3.0 UBL 2.1
}
GUIDELINE_TO_PROFILE = {v: k for k, v in PROFILE_TO_GUIDELINE.items()}

# Map of EInvoiceProfile to XSD Schema name (for PEPPOL)
PROFILE_TO_XSD_SCHEMA = {
	EInvoiceProfile.PEPPOL: "UBL-Invoice-2.1",  # PEPPOL uses UBL 2.1 XSD validation
}


def get_xsd_schema(profile: EInvoiceProfile) -> str:
	"""Return the XSD schema name for PEPPOL profile."""
	return PROFILE_TO_XSD_SCHEMA.get(profile)


def get_drafthorse_schema(profile: EInvoiceProfile) -> str:
	"""Return the drafthorse schema name for Factur-X profiles (BASIC, EN16931, XRECHNUNG, EXTENDED)."""
	return PROFILE_TO_SCHEMA.get(profile)


def get_guideline(profile: EInvoiceProfile) -> str:
	"""Return the guideline for the given profile."""
	return PROFILE_TO_GUIDELINE.get(profile)


def get_profile(guideline: str) -> EInvoiceProfile:
	"""Return the profile for the given guideline."""
	return GUIDELINE_TO_PROFILE.get(guideline)


def get_profile_from_xml(xml_bytes: bytes) -> EInvoiceProfile | None:
	"""
	Utility function to detect e-invoice profile from XML bytes.
	"""
	# Try CII format first (Factur-X)
	try:
		from drafthorse.models.document import Document as DrafthorseDocument
		doc = DrafthorseDocument.parse(xml_bytes, strict=False)
		guideline = doc.context.guideline_parameter.id._text
		return get_profile(guideline)  # Uses GUIDELINE_TO_PROFILE mapping
	except Exception:
		pass
	
	# Try PEPPOL format (UBL 2.1)
	try:
		from lxml import etree as ET
		from eu_einvoice.peppol import UBL_NAMESPACES
		root = ET.fromstring(xml_bytes)
		customization_id_elem = root.find('.//cbc:CustomizationID', UBL_NAMESPACES)
		if customization_id_elem is not None and customization_id_elem.text:
			customization_id = customization_id_elem.text
			return get_profile(customization_id)  # Uses GUIDELINE_TO_PROFILE mapping
	except Exception:
		pass
	
	return None


def get_xml_text(element, xpath, namespaces=None) -> str | None:
	if element is None:
		return None
	result = element.find(xpath, namespaces or {})
	return result.text if result is not None and result.text else None


def identity(value):
	"""Used for dummy translation"""
	return value
