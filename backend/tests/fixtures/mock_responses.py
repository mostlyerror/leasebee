"""
Mock responses for external services (Claude API, S3, etc.)

This module contains realistic mock data used in tests to simulate
responses from external services without making actual API calls.
"""

# ============================================================================
# Claude API Mock Responses
# ============================================================================

MOCK_CLAUDE_EXTRACTION_COMPLETE = {
    """Complete extraction response with all fields populated."""
    "extractions": {
        # Tenant Information
        "tenant.name": "Acme Corporation",
        "tenant.address": "123 Business Park, Suite 100",
        "tenant.city": "San Francisco",
        "tenant.state": "CA",
        "tenant.zip": "94105",
        "tenant.contact_name": "John Smith",
        "tenant.contact_email": "john.smith@acmecorp.com",
        "tenant.contact_phone": "415-555-0123",

        # Landlord Information
        "landlord.name": "Property Management LLC",
        "landlord.address": "456 Commercial Plaza",
        "landlord.city": "San Francisco",
        "landlord.state": "CA",
        "landlord.zip": "94102",
        "landlord.contact_name": "Jane Doe",
        "landlord.contact_email": "jane.doe@propertymanagement.com",
        "landlord.contact_phone": "415-555-0456",

        # Property Information
        "property.address": "789 Office Boulevard, Suite 200",
        "property.city": "San Francisco",
        "property.state": "CA",
        "property.zip": "94103",
        "property.square_feet": "5000",
        "property.type": "Office",
        "property.floor": "2",
        "property.building_name": "Tech Center Plaza",

        # Financial Terms
        "financial.base_rent": "15000.00",
        "financial.rent_frequency": "Monthly",
        "financial.security_deposit": "30000.00",
        "financial.rent_escalation": "3% annually",
        "financial.additional_rent": "Common area maintenance",
        "financial.operating_expenses": "Prorated share",
        "financial.late_fee": "5% after 5 days",
        "financial.payment_method": "ACH transfer",

        # Lease Terms
        "lease_terms.start_date": "2024-01-01",
        "lease_terms.end_date": "2026-12-31",
        "lease_terms.term_length": "36 months",
        "lease_terms.renewal_option": "Two 12-month options",
        "lease_terms.notice_period": "180 days",
        "lease_terms.lease_type": "Triple Net",

        # Special Provisions
        "special_provisions.parking_spaces": "10",
        "special_provisions.parking_cost": "Included",
        "special_provisions.utilities_included": "Water and sewer",
        "special_provisions.maintenance_responsibility": "Landlord handles exterior, tenant handles interior",
        "special_provisions.subleasing_allowed": "With written consent",
        "special_provisions.improvements_allowance": "$50,000",
        "special_provisions.signage_rights": "Building directory and exterior sign",
    },
    "reasoning": {
        "tenant.name": "Found in the preamble section of the lease agreement, clearly identified as the 'Tenant' party.",
        "tenant.address": "Listed under Tenant's Notice Address in Section 12.1",
        "landlord.name": "Identified in the preamble as the 'Landlord' party to the agreement.",
        "property.address": "Specified in Section 1.1 as the 'Premises' being leased.",
        "financial.base_rent": "Explicitly stated in Section 4.1: Rent, with monthly payment amount.",
        "financial.security_deposit": "Section 5: Security Deposit specifies the amount held by Landlord.",
        "lease_terms.start_date": "Commencement Date defined in Section 2.1",
        "lease_terms.end_date": "Expiration Date calculated from the 36-month term starting January 1, 2024.",
        "lease_terms.renewal_option": "Section 3.2 outlines tenant's right to extend the lease.",
        "property.square_feet": "Premises description in Section 1.1 states approximately 5,000 rentable square feet.",
        "special_provisions.parking_spaces": "Section 8: Parking specifies ten (10) designated parking spaces.",
    },
    "citations": {
        "tenant.name": {
            "page": 1,
            "quote": "This Lease Agreement ('Lease') is entered into by and between Property Management LLC ('Landlord') and Acme Corporation ('Tenant')",
            "section": "Preamble"
        },
        "landlord.name": {
            "page": 1,
            "quote": "This Lease Agreement ('Lease') is entered into by and between Property Management LLC ('Landlord') and Acme Corporation ('Tenant')",
            "section": "Preamble"
        },
        "property.address": {
            "page": 1,
            "quote": "Landlord hereby leases to Tenant, and Tenant hereby leases from Landlord, those certain premises located at 789 Office Boulevard, Suite 200, San Francisco, CA 94103",
            "section": "Section 1.1 - Premises"
        },
        "financial.base_rent": {
            "page": 2,
            "quote": "Tenant shall pay Base Rent of Fifteen Thousand Dollars ($15,000.00) per month, due on the first day of each calendar month",
            "section": "Section 4.1 - Base Rent"
        },
        "financial.security_deposit": {
            "page": 2,
            "quote": "Upon execution of this Lease, Tenant shall deposit with Landlord the sum of Thirty Thousand Dollars ($30,000.00) as a security deposit",
            "section": "Section 5 - Security Deposit"
        },
        "lease_terms.start_date": {
            "page": 1,
            "quote": "The Lease Term shall commence on January 1, 2024 ('Commencement Date')",
            "section": "Section 2.1 - Term"
        },
        "lease_terms.end_date": {
            "page": 1,
            "quote": "and shall continue for a period of thirty-six (36) months, ending on December 31, 2026 ('Expiration Date')",
            "section": "Section 2.1 - Term"
        },
        "lease_terms.renewal_option": {
            "page": 2,
            "quote": "Tenant shall have two (2) options to extend the Lease Term for additional periods of twelve (12) months each",
            "section": "Section 3.2 - Renewal Options"
        },
        "property.square_feet": {
            "page": 1,
            "quote": "The Premises consist of approximately five thousand (5,000) rentable square feet",
            "section": "Section 1.1 - Premises"
        },
        "special_provisions.parking_spaces": {
            "page": 3,
            "quote": "Landlord shall provide Tenant with ten (10) designated parking spaces in the building's parking facility",
            "section": "Section 8 - Parking"
        },
    },
    "confidence": {
        "tenant.name": 0.99,
        "tenant.address": 0.97,
        "tenant.city": 0.98,
        "tenant.state": 0.99,
        "tenant.zip": 0.98,
        "landlord.name": 0.99,
        "landlord.address": 0.96,
        "property.address": 0.99,
        "property.city": 0.99,
        "property.state": 0.99,
        "property.square_feet": 0.95,
        "financial.base_rent": 0.99,
        "financial.security_deposit": 0.99,
        "financial.rent_escalation": 0.92,
        "lease_terms.start_date": 0.99,
        "lease_terms.end_date": 0.98,
        "lease_terms.term_length": 0.99,
        "lease_terms.renewal_option": 0.94,
        "special_provisions.parking_spaces": 0.97,
    }
}


MOCK_CLAUDE_EXTRACTION_PARTIAL = {
    """Partial extraction response with some missing fields (realistic scenario)."""
    "extractions": {
        "tenant.name": "Tech Startup Inc.",
        "landlord.name": "Real Estate Holdings Corp.",
        "property.address": "555 Innovation Drive",
        "financial.base_rent": "8500.00",
        "lease_terms.start_date": "2024-06-01",
        "lease_terms.term_length": "24 months",
    },
    "reasoning": {
        "tenant.name": "Clearly identified in lease header",
        "financial.base_rent": "Found in rent section, but escalation terms unclear",
        "lease_terms.start_date": "Commencement date explicitly stated",
    },
    "citations": {
        "tenant.name": {
            "page": 1,
            "quote": "between Real Estate Holdings Corp. and Tech Startup Inc.",
            "section": "Header"
        },
        "financial.base_rent": {
            "page": 3,
            "quote": "Monthly rent: $8,500",
            "section": "Rent"
        },
    },
    "confidence": {
        "tenant.name": 0.98,
        "landlord.name": 0.97,
        "property.address": 0.85,
        "financial.base_rent": 0.96,
        "lease_terms.start_date": 0.99,
        "lease_terms.term_length": 0.88,
    }
}


MOCK_CLAUDE_EXTRACTION_ERROR = {
    """Error response when Claude cannot extract data."""
    "error": "Unable to extract lease data",
    "reason": "Document does not appear to be a lease agreement",
    "extractions": {},
    "reasoning": {},
    "citations": {},
    "confidence": {}
}


# ============================================================================
# S3 Mock Responses
# ============================================================================

MOCK_S3_UPLOAD_RESPONSE = {
    "ResponseMetadata": {
        "RequestId": "mock-request-id-12345",
        "HTTPStatusCode": 200,
    },
    "ETag": '"mock-etag-67890"',
}


MOCK_S3_GET_OBJECT_RESPONSE = {
    "Body": None,  # Will be replaced with actual bytes in fixture
    "ContentLength": 1024,
    "ContentType": "application/pdf",
    "ETag": '"mock-etag-67890"',
}


# ============================================================================
# Expected API Response Schemas
# ============================================================================

EXPECTED_LEASE_UPLOAD_RESPONSE = {
    "id": 1,
    "filename": "test-uuid-12345678.pdf",
    "original_filename": "test.pdf",
    "file_size": 1024,
    "status": "uploaded",
    "created_at": "2024-01-01T00:00:00",
}


EXPECTED_EXTRACTION_RESPONSE = {
    "id": 1,
    "lease_id": 1,
    "extractions": {},  # Will contain extracted fields
    "reasoning": {},
    "citations": {},
    "confidence": {},
    "model_version": "claude-3-5-sonnet-20241022",
    "created_at": "2024-01-01T00:00:00",
}
