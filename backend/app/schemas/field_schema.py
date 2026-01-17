"""
Lease field schema definition.

This file defines all fields to be extracted from commercial leases.
It serves as the single source of truth for:
- Extraction prompts
- UI generation
- Validation
- Export formatting
"""
from typing import Dict, List, Any
from enum import Enum


class FieldType(str, Enum):
    """Field data types."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    AREA = "area"  # Square feet, acres, etc.
    ADDRESS = "address"
    LIST = "list"  # Multiple values


class FieldCategory(str, Enum):
    """Field categories for organization."""
    BASIC_INFO = "basic_info"
    PARTIES = "parties"
    PROPERTY = "property"
    FINANCIAL = "financial"
    DATES_TERM = "dates_term"
    RENT = "rent"
    OPERATING_EXPENSES = "operating_expenses"
    RIGHTS_OPTIONS = "rights_options"
    USE_RESTRICTIONS = "use_restrictions"
    MAINTENANCE = "maintenance"
    INSURANCE = "insurance"
    OTHER = "other"


# Field schema definition
# This is a simplified starter schema - should be customized with actual client requirements
LEASE_FIELDS: List[Dict[str, Any]] = [
    # Basic Information
    {
        "path": "basic_info.lease_type",
        "label": "Lease Type",
        "category": FieldCategory.BASIC_INFO,
        "type": FieldType.TEXT,
        "description": "Type of lease (e.g., Office, Retail, Industrial, Ground)",
        "required": True,
    },
    {
        "path": "basic_info.execution_date",
        "label": "Execution Date",
        "category": FieldCategory.BASIC_INFO,
        "type": FieldType.DATE,
        "description": "Date the lease was executed/signed",
        "required": True,
    },

    # Parties
    {
        "path": "parties.landlord_name",
        "label": "Landlord Name",
        "category": FieldCategory.PARTIES,
        "type": FieldType.TEXT,
        "description": "Full legal name of the landlord/lessor",
        "required": True,
    },
    {
        "path": "parties.landlord_address",
        "label": "Landlord Address",
        "category": FieldCategory.PARTIES,
        "type": FieldType.ADDRESS,
        "description": "Mailing address of the landlord",
        "required": False,
    },
    {
        "path": "parties.tenant_name",
        "label": "Tenant Name",
        "category": FieldCategory.PARTIES,
        "type": FieldType.TEXT,
        "description": "Full legal name of the tenant/lessee",
        "required": True,
    },
    {
        "path": "parties.tenant_address",
        "label": "Tenant Address",
        "category": FieldCategory.PARTIES,
        "type": FieldType.ADDRESS,
        "description": "Mailing address of the tenant",
        "required": False,
    },

    # Property Information
    {
        "path": "property.address",
        "label": "Property Address",
        "category": FieldCategory.PROPERTY,
        "type": FieldType.ADDRESS,
        "description": "Full street address of the leased property",
        "required": True,
    },
    {
        "path": "property.suite_unit",
        "label": "Suite/Unit Number",
        "category": FieldCategory.PROPERTY,
        "type": FieldType.TEXT,
        "description": "Specific suite or unit number if applicable",
        "required": False,
    },
    {
        "path": "property.rentable_area",
        "label": "Rentable Square Feet",
        "category": FieldCategory.PROPERTY,
        "type": FieldType.AREA,
        "description": "Rentable square footage of the premises",
        "required": True,
    },
    {
        "path": "property.usable_area",
        "label": "Usable Square Feet",
        "category": FieldCategory.PROPERTY,
        "type": FieldType.AREA,
        "description": "Usable square footage of the premises",
        "required": False,
    },

    # Dates and Term
    {
        "path": "dates.commencement_date",
        "label": "Commencement Date",
        "category": FieldCategory.DATES_TERM,
        "type": FieldType.DATE,
        "description": "Date when the lease term begins",
        "required": True,
    },
    {
        "path": "dates.expiration_date",
        "label": "Expiration Date",
        "category": FieldCategory.DATES_TERM,
        "type": FieldType.DATE,
        "description": "Date when the lease term ends",
        "required": True,
    },
    {
        "path": "dates.rent_commencement_date",
        "label": "Rent Commencement Date",
        "category": FieldCategory.DATES_TERM,
        "type": FieldType.DATE,
        "description": "Date when rent payments begin (may differ from lease commencement)",
        "required": False,
    },
    {
        "path": "dates.lease_term_months",
        "label": "Lease Term (Months)",
        "category": FieldCategory.DATES_TERM,
        "type": FieldType.NUMBER,
        "description": "Total length of the lease term in months",
        "required": True,
    },

    # Rent
    {
        "path": "rent.base_rent_monthly",
        "label": "Base Rent (Monthly)",
        "category": FieldCategory.RENT,
        "type": FieldType.CURRENCY,
        "description": "Monthly base rent amount",
        "required": True,
    },
    {
        "path": "rent.base_rent_annual",
        "label": "Base Rent (Annual)",
        "category": FieldCategory.RENT,
        "type": FieldType.CURRENCY,
        "description": "Annual base rent amount",
        "required": False,
    },
    {
        "path": "rent.rent_per_sf_annual",
        "label": "Rent per SF (Annual)",
        "category": FieldCategory.RENT,
        "type": FieldType.CURRENCY,
        "description": "Annual rent per square foot",
        "required": False,
    },
    {
        "path": "rent.rent_escalations",
        "label": "Rent Escalations",
        "category": FieldCategory.RENT,
        "type": FieldType.TEXT,
        "description": "Description of rent increase schedule or formula",
        "required": False,
    },
    {
        "path": "rent.free_rent_months",
        "label": "Free Rent Period (Months)",
        "category": FieldCategory.RENT,
        "type": FieldType.NUMBER,
        "description": "Number of months of free rent, if any",
        "required": False,
    },

    # Operating Expenses
    {
        "path": "operating_expenses.structure_type",
        "label": "Operating Expense Structure",
        "category": FieldCategory.OPERATING_EXPENSES,
        "type": FieldType.TEXT,
        "description": "Type of operating expense structure (e.g., NNN, Gross, Modified Gross)",
        "required": False,
    },
    {
        "path": "operating_expenses.base_year",
        "label": "Base Year for Operating Expenses",
        "category": FieldCategory.OPERATING_EXPENSES,
        "type": FieldType.TEXT,
        "description": "Base year for calculating operating expense increases",
        "required": False,
    },
    {
        "path": "operating_expenses.tenant_share_percentage",
        "label": "Tenant's Share Percentage",
        "category": FieldCategory.OPERATING_EXPENSES,
        "type": FieldType.PERCENTAGE,
        "description": "Tenant's proportionate share of operating expenses",
        "required": False,
    },

    # Financial
    {
        "path": "financial.security_deposit",
        "label": "Security Deposit",
        "category": FieldCategory.FINANCIAL,
        "type": FieldType.CURRENCY,
        "description": "Amount of security deposit required",
        "required": False,
    },
    {
        "path": "financial.tenant_improvement_allowance",
        "label": "Tenant Improvement Allowance",
        "category": FieldCategory.FINANCIAL,
        "type": FieldType.CURRENCY,
        "description": "Amount landlord will contribute for tenant improvements",
        "required": False,
    },

    # Rights and Options
    {
        "path": "rights.renewal_options",
        "label": "Renewal Options",
        "category": FieldCategory.RIGHTS_OPTIONS,
        "type": FieldType.TEXT,
        "description": "Description of renewal option terms",
        "required": False,
    },
    {
        "path": "rights.termination_rights",
        "label": "Termination Rights",
        "category": FieldCategory.RIGHTS_OPTIONS,
        "type": FieldType.TEXT,
        "description": "Any early termination rights or conditions",
        "required": False,
    },
    {
        "path": "rights.expansion_rights",
        "label": "Expansion Rights",
        "category": FieldCategory.RIGHTS_OPTIONS,
        "type": FieldType.TEXT,
        "description": "Rights to expand into additional space",
        "required": False,
    },

    # Use and Restrictions
    {
        "path": "use.permitted_use",
        "label": "Permitted Use",
        "category": FieldCategory.USE_RESTRICTIONS,
        "type": FieldType.TEXT,
        "description": "Permitted uses of the premises",
        "required": False,
    },
    {
        "path": "use.exclusive_use",
        "label": "Exclusive Use Rights",
        "category": FieldCategory.USE_RESTRICTIONS,
        "type": FieldType.TEXT,
        "description": "Any exclusive use rights granted to tenant",
        "required": False,
    },

    # Maintenance and Repairs
    {
        "path": "maintenance.landlord_responsibilities",
        "label": "Landlord Maintenance Responsibilities",
        "category": FieldCategory.MAINTENANCE,
        "type": FieldType.TEXT,
        "description": "What the landlord is responsible for maintaining",
        "required": False,
    },
    {
        "path": "maintenance.tenant_responsibilities",
        "label": "Tenant Maintenance Responsibilities",
        "category": FieldCategory.MAINTENANCE,
        "type": FieldType.TEXT,
        "description": "What the tenant is responsible for maintaining",
        "required": False,
    },

    # Insurance
    {
        "path": "insurance.tenant_insurance_requirements",
        "label": "Tenant Insurance Requirements",
        "category": FieldCategory.INSURANCE,
        "type": FieldType.TEXT,
        "description": "Insurance coverage tenant must maintain",
        "required": False,
    },

    # Other Important Terms
    {
        "path": "other.parking_spaces",
        "label": "Parking Spaces",
        "category": FieldCategory.OTHER,
        "type": FieldType.NUMBER,
        "description": "Number of parking spaces allocated to tenant",
        "required": False,
    },
    {
        "path": "other.parking_cost",
        "label": "Parking Cost",
        "category": FieldCategory.OTHER,
        "type": FieldType.CURRENCY,
        "description": "Cost per parking space, if applicable",
        "required": False,
    },
]


def get_field_by_path(path: str) -> Dict[str, Any]:
    """Get field definition by path."""
    for field in LEASE_FIELDS:
        if field["path"] == path:
            return field
    return None


def get_fields_by_category(category: FieldCategory) -> List[Dict[str, Any]]:
    """Get all fields in a category."""
    return [f for f in LEASE_FIELDS if f["category"] == category]


def get_required_fields() -> List[Dict[str, Any]]:
    """Get all required fields."""
    return [f for f in LEASE_FIELDS if f.get("required", False)]


def get_field_paths() -> List[str]:
    """Get list of all field paths."""
    return [f["path"] for f in LEASE_FIELDS]


def get_schema_for_claude() -> str:
    """
    Generate a formatted schema description for Claude's prompt.

    Returns:
        Formatted string describing the schema for extraction.
    """
    schema_parts = []

    # Group by category
    categories = {}
    for field in LEASE_FIELDS:
        cat = field["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(field)

    # Format each category
    for category, fields in categories.items():
        schema_parts.append(f"\n## {category.value.replace('_', ' ').title()}")
        for field in fields:
            required = " (REQUIRED)" if field.get("required", False) else ""
            schema_parts.append(
                f"- {field['path']}: {field['description']}{required}"
            )

    return "\n".join(schema_parts)
