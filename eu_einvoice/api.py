"""
API endpoints for PEPPOL e-invoicing functionality.

This module provides API endpoints that can be called from the frontend
for PEPPOL operations including B2B Router transmission.
"""

import frappe
from frappe import _
import json
from typing import Dict, Any

from .peppol.generator import PEPPOLGenerator
from .peppol.b2brouter_api import get_b2b_router_client, validate_api_connection


@frappe.whitelist()
def validate_peppol_connection():
    """
    Validate B2B Router API connection.

    Returns:
        Connection validation result
    """
    try:
        result = validate_api_connection()
        return result
    except Exception as e:
        frappe.log_error(f"PEPPOL connection validation error: {str(e)}", "PEPPOL API Error")
        return {
            "status": "error",
            "message": f"Connection validation failed: {str(e)}"
        }


@frappe.whitelist()
def get_e_invoice_integration_settings(profile, company=None):
    """
    Get E Invoice Integration Settings for the given profile.

    Args:
        profile: E-invoice profile (e.g., 'PEPPOL')
        company: Optional company filter

    Returns:
        Dictionary with integration settings or None if not found
    """
    filters = {"einvoice_profile": profile}
    if company:
        filters["company"] = company
    
    settings = frappe.get_all(
        "E Invoice Integration Settings",
        filters=filters,
        fields=["api_key", "api_secret", "base_url", "einvoice_integrator", "company", "account_id", "company_id"]
    )

    if settings:
        return settings[0]
    return None


@frappe.whitelist()
def transmit_e_invoice(invoice_name):
    """
    Transmit E-invoice using the configured integrator.

    Args:
        invoice_name: Name of the Sales Invoice document

    Returns:
        Transmission result
    """
    try:
        # Get the invoice document
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)

        # Validate invoice
        if not invoice_doc.einvoice_is_correct:
            return {
                "status": "error",
                "message": _("Invoice is not validated for e-invoicing. Please validate first.")
            }

        # Get e-invoice profile
        profile = invoice_doc.einvoice_profile
        if not profile:
            return {
                "status": "error",
                "message": _("No e-invoice profile configured for this invoice.")
            }

        # Generate XML using existing get_einvoice function
        from .european_e_invoice.custom.sales_invoice import get_einvoice
        xml_content = get_einvoice(invoice_name)

        # Get integration settings for this profile
        integration_settings = get_e_invoice_integration_settings(profile, invoice_doc.company)

        if not integration_settings:
            return {
                "status": "error",
                "message": _("No integration settings found for profile: {0}").format(profile)
            }

        integrator = integration_settings.get('einvoice_integrator')

        # Route to appropriate integrator with XML content
        transmission_result = None
        
        if integrator == 'B2B Router':
            try:
                # Get B2B Router client using integration settings
                api_key = integration_settings.get('api_key')
                base_url = integration_settings.get('base_url', 'https://api.b2brouter.net/v1/')

                if not api_key:
                    return {
                        "status": "error",
                        "message": _("API key not configured in E Invoice Integration Settings")
                    }

                from .peppol.b2brouter_api import B2BRouterAPIClient
                b2b_client = B2BRouterAPIClient(api_key, base_url)

                # Pass integration settings to B2B Router client
                transmission_result = b2b_client.transmit_invoice(
                    xml_content, 
                    invoice_doc=invoice_doc, 
                    integration_settings=integration_settings
                )
                
            except Exception as e:
                error_msg = f"B2B Router transmission failed: {str(e)}"
                frappe.log_error(error_msg, "B2B Router Transmission Error")
                return {
                    "status": "error",
                    "message": error_msg
                }
                
        elif integrator == 'Recommand':
            try:
                # Get Recommand client using integration settings
                from .peppol.recommand_api import transmit_invoice
                transmission_result = transmit_invoice(
                    xml_content, 
                    invoice_doc=invoice_doc, 
                    integration_settings=integration_settings
                )
                
            except Exception as e:
                error_msg = f"Recommand transmission failed: {str(e)}"
                frappe.log_error(error_msg, "Recommand Transmission Error")
                return {
                    "status": "error",
                    "message": error_msg
                }
        else:
            return {
                "status": "error",
                "message": _("Unsupported E-invoice integrator: {0}").format(integrator)
            }

        # Add transmission details as comment on the invoice (for both integrators)
        transmission_id = transmission_result.get('id') or transmission_result.get('document_id')
        tracking_id = transmission_result.get('tracking_id', transmission_result.get('id'))
        status = transmission_result.get('status', 'transmitted')
        estimated_delivery = transmission_result.get('estimated_delivery')
        recipient = transmission_result.get('recipient')

        comment_text = f"""✅ E-invoice Transmission Successful:
• Transmission ID: {transmission_id}
• Tracking ID: {tracking_id}
• Status: {status}"""

        if estimated_delivery:
            comment_text += f"\n• Estimated Delivery: {estimated_delivery}"

        if recipient:
            comment_text += f"\n• Recipient: {recipient}"

        # Add comment to the invoice
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
        invoice_doc.add_comment(
            comment_type="Info",
            text=comment_text
        )
            
        return transmission_result

    except Exception as e:
        error_msg = f"E-invoice transmission failed for invoice {invoice_name}: {str(e)}"
        frappe.log_error(error_msg, "E-invoice Transmission Error")
        return {
            "status": "error",
            "message": _("Transmission failed: {0}").format(str(e))
        }




@frappe.whitelist()
def check_transmission_status(invoice_name: str) -> Dict[str, Any]:
    """
    Check transmission status for an E-invoice.

    Args:
        invoice_name: Name of the Sales Invoice document

    Returns:
        Transmission status information
    """
    try:
        # Get the invoice document
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)

        # Get integration settings for this profile
        integration_settings = get_e_invoice_integration_settings(invoice_doc.einvoice_profile, invoice_doc.company)

        if not integration_settings:
            return {
                "status": "error",
                "message": _("No integration settings found for profile: {0}").format(invoice_doc.einvoice_profile)
            }

        integrator = integration_settings.get('einvoice_integrator')

        # Route to appropriate integrator
        if integrator == 'B2B Router':
            return check_transmission_status_b2b_router(invoice_name, integration_settings)
        else:
            return {
                "status": "error",
                "message": _("Unsupported E-invoice integrator: {0}").format(integrator)
            }

    except Exception as e:
        error_msg = f"Status check failed for invoice {invoice_name}: {str(e)}"
        frappe.log_error(error_msg, "E-invoice Status Check Error")

        return {
            "status": "error",
            "message": _("Status check failed: {0}").format(str(e))
        }


def check_transmission_status_b2b_router(invoice_name: str, integration_settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check transmission status using B2B Router.

    Args:
        invoice_name: Name of the Sales Invoice document
        integration_settings: Integration settings from E Invoice Integration Settings doctype

    Returns:
        Transmission status information
    """
    try:
        # Get the invoice document
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)

        # Get B2B Router client using integration settings
        api_key = integration_settings.get('api_key')
        base_url = integration_settings.get('base_url', 'https://api.b2brouter.net/v1/')

        if not api_key:
            raise Exception("API key not configured in E Invoice Integration Settings")

        from .peppol.b2brouter_api import B2BRouterAPIClient
        b2b_client = B2BRouterAPIClient(api_key, base_url)

        # For now, return a placeholder response since we don't have transmission tracking implemented
        # In a real implementation, you would check the actual transmission status
        return {
            "status": "success",
            "message": _("Status check not yet implemented for B2B Router"),
            "transmission_status": "unknown",
            "recipient_status": "unknown",
            "delivery_timestamp": None,
            "recipient_response": None,
            "errors": []
        }

    except Exception as e:
        error_msg = f"B2B Router status check failed for invoice {invoice_name}: {str(e)}"
        frappe.log_error(error_msg, "B2B Router Status Check Error")
        raise


@frappe.whitelist()
def get_transmission_history(invoice_name: str) -> Dict[str, Any]:
    """
    Get detailed transmission history for a PEPPOL invoice.

    Args:
        invoice_name: Name of the Sales Invoice document

    Returns:
        Transmission history details
    """
    try:
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)

        if not hasattr(invoice_doc, 'peppol_transmission_id') or not invoice_doc.peppol_transmission_id:
            return {
                "status": "error",
                "message": _("Invoice has not been transmitted yet.")
            }

        # Get B2B Router client
        b2b_client = get_b2b_router_client()

        # Get history
        history_result = b2b_client.get_invoice_history(invoice_doc.peppol_transmission_id)

        return {
            "status": "success",
            "history": history_result
        }

    except Exception as e:
        error_msg = f"History retrieval failed for invoice {invoice_name}: {str(e)}"
        frappe.log_error(error_msg, "PEPPOL History Error")

        return {
            "status": "error",
            "message": f"History retrieval failed: {str(e)}"
        }


@frappe.whitelist()
def cancel_transmission(invoice_name: str, reason: str = "") -> Dict[str, Any]:
    """
    Cancel a pending PEPPOL transmission.

    Args:
        invoice_name: Name of the Sales Invoice document
        reason: Reason for cancellation

    Returns:
        Cancellation result
    """
    try:
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)

        if not hasattr(invoice_doc, 'peppol_transmission_id') or not invoice_doc.peppol_transmission_id:
            return {
                "status": "error",
                "message": _("Invoice has not been transmitted yet.")
            }

        # Get B2B Router client
        b2b_client = get_b2b_router_client()

        # Cancel transmission
        cancel_result = b2b_client.cancel_invoice(invoice_doc.peppol_transmission_id, reason)

        # Update invoice status
        invoice_doc.peppol_transmission_status = 'cancelled'
        invoice_doc.save()

        return {
            "status": "success",
            "message": _("Transmission cancelled successfully"),
            "cancel_result": cancel_result
        }

    except Exception as e:
        error_msg = f"Transmission cancellation failed for invoice {invoice_name}: {str(e)}"
        frappe.log_error(error_msg, "PEPPOL Cancellation Error")

        return {
            "status": "error",
            "message": f"Cancellation failed: {str(e)}"
        }


@frappe.whitelist()
def get_transmission_report(date_from: str, date_to: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get transmission report for date range.

    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        filters: Optional filters

    Returns:
        Transmission report data
    """
    try:
        # Get B2B Router client
        b2b_client = get_b2b_router_client()

        # Get report
        report = b2b_client.get_transmission_report(date_from, date_to, filters)

        return {
            "status": "success",
            "report": report
        }

    except Exception as e:
        error_msg = f"Report generation failed: {str(e)}"
        frappe.log_error(error_msg, "PEPPOL Report Error")

        return {
            "status": "error",
            "message": f"Report generation failed: {str(e)}"
        }


