"""seed default prompt template from hardcoded values

Revision ID: 006_seed_prompt
Revises: 005_prompt_templates
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '006_seed_prompt'
down_revision = '005_prompt_templates'
branch_labels = None
depends_on = None


# Current hardcoded prompt sections from claude_service.py

SYSTEM_PROMPT = """You are a commercial lease abstraction expert. Extract structured information from this lease PDF.

For each field in the schema below:
1. Extract the exact value from the document
2. Explain your reasoning - why did you extract this specific value?
3. Cite the specific section (page number and brief quote) where you found it
4. Rate your confidence (0.0-1.0) based on how clear the information is

If a field is not present or cannot be determined from the document, set the value to null and explain why in the reasoning.

CRITICAL: Return ONLY valid JSON. Do not include any text before or after the JSON object.

Return a JSON object with this EXACT structure:
{
  "extractions": {"field_path": "value"},
  "reasoning": {"field_path": "explanation"},
  "citations": {"field_path": {"page": number, "quote": "brief relevant quote"}},
  "confidence": {"field_path": 0.95}
}"""

FIELD_TYPE_GUIDANCE = """\
=== CRITICAL EXTRACTION GUIDELINES ===

EXECUTION DATE (basic_info.execution_date):
-- CRITICAL: Check signature blocks at the end of the document
-- Look for: "Dated:", "Executed:", "Date Signed:" near signatures
-- Common locations: Last page, signature page, execution clause
-- Format: YYYY-MM-DD (convert from "December 15, 2023" -> "2023-12-15")
-- If different dates for landlord/tenant, use the later date
-- If "as of" date precedes signatures, that's the execution date

DATES:
- Format: Always return ISO format YYYY-MM-DD
- Common locations: Look in "Term", "Lease Period", or first page summary
- Handle variations: "January 1, 2024" -> "2024-01-01", "1/1/24" -> "2024-01-01"
- TBD dates: If date is "TBD", "upon completion", or "to be determined", set to null
- Expiration calculation: If only term length given, calculate from commencement date
- Confidence: High (0.95+) only if exact date stated, Medium (0.7-0.9) if calculated

CURRENCY (Rent, Deposits, Allowances):
- Format: Numeric value only, no symbols. Use "." for decimals (e.g., "15000.00")
- Per-month to annual: If "per month", multiply by 12 for annual fields
- Look for: Dollar signs, "rent", "deposit", financial tables
- Free rent: If "first month free" or rent abatement, note in reasoning
- Escalations: Extract base rent separate from escalated amounts
- Confidence: High (0.95+) if in table/schedule, Medium (0.7-0.9) if in paragraph

TENANT IMPROVEMENT ALLOWANCE (financial.tenant_improvement_allowance):
- CRITICAL: Check exhibits, schedules, and work letter attachments
- Look for: "TI Allowance", "Improvement Allowance", "Construction Allowance"
- Common locations: Exhibit A, Work Letter, Construction Rider, Lease Schedule
- Also check: "Landlord shall provide", "allowance for improvements", "build-out allowance"
- Format: Numeric value only (e.g., "50000.00" not "$50,000" or "50k")
- If stated as "per square foot", multiply by total square footage
- If not mentioned anywhere, set to null with reasoning "Not specified in lease"

SQUARE FOOTAGE / AREA:
- Format: Numeric value only, no "SF" or "square feet" (e.g., "5000")
- RSF vs USF: Rentable vs Usable - extract to correct field
- Common locations: Property description, first page, exhibits, rent calculations
- Look for: "rentable square feet", "RSF", "usable square feet", "USF"
- Variations: "5,000 SF" -> "5000", "Five thousand square feet" -> "5000"
- Confidence: High (0.95+) if explicitly stated, Medium (0.7-0.9) if calculated from rent/SF

ADDRESSES:
- Format: Full street address with city, state, ZIP
- Suite/unit: Extract separately to suite_unit field, not in main address
- Look for: First page, "Premises", "Property Description"
- Example: "123 Main St, Suite 200, San Francisco, CA 94105"
  -> property.address: "123 Main St, San Francisco, CA 94105"
  -> property.suite_unit: "Suite 200"
- Confidence: High (0.95+) for complete address

PARTIES (Landlord, Tenant):
- Names: Extract full legal name as written (include "LLC", "Inc", etc)
- Look for: First page, "between", signature blocks, "Landlord" and "Tenant" labels
- Avoid: Don't extract contact persons, only entity names
- Example: "ABC Properties, LLC" not "John Smith of ABC Properties"
- Addresses: Extract party addresses separately
- Confidence: High (0.95+) for names on first page

PERCENTAGES:
- Format: Decimal (0.05 for 5%, not "5" or "5%")
- Look for: Rent increases, tenant's share, parking ratio
- Context: "5% annual increase" -> "0.05", "Tenant's 12.5% share" -> "0.125"
- Confidence: High (0.95+) if explicit percentage

BOOLEAN FIELDS:
- Format: true or false (lowercase)
- Look for: "NNN", "gross lease", "shall"/"shall not"
- If ambiguous or unclear, set to null
- Confidence: Only high (0.9+) if explicitly stated

PERMITTED USE (use.permitted_use):
- Look for: "Use", "Permitted Use", "Purpose", "Use Restrictions" clauses
- Common locations: Section on Use, early in the lease, or exhibit
- Extract the full description (e.g., "General office use", "Retail sales of consumer goods")
- Include any restrictions: "and no other purpose", "only for", "restricted to"
- If broad/generic like "any lawful purpose", extract that exact phrase
- If multiple uses listed, include all separated by commas

MAINTENANCE RESPONSIBILITIES (maintenance.landlord_responsibilities, maintenance.tenant_responsibilities):
- CRITICAL: Check "Maintenance", "Repairs", "Services" sections carefully
- Look for: Exhibits on maintenance, schedules outlining responsibilities
- Landlord typically: HVAC, structural, roof, exterior, common areas, building systems
- Tenant typically: Interior, fixtures, glass, non-structural elements
- Extract: Full description of each party's responsibilities
- Example format: "Landlord: HVAC, roof, structural. Tenant: interior, fixtures, cleaning"
- Check both: Main lease body AND exhibits/schedules
- If responsibilities are split by item, list items for each party

PARKING (other.parking_spaces, other.parking_cost):
- CRITICAL: Check exhibits, schedules, and "Parking" sections
- Common locations: Exhibit B (Parking), Lease Schedule, Amenities section
- Look for: "parking spaces", "parking allocation", "parking rights"
- parking_spaces: Number only (e.g., "10" not "10 spaces")
- parking_cost: "0" if free/included, otherwise numeric value
- If "unassigned" or "shared", note in reasoning but extract available count
- Check: "Tenant shall have the right to use X parking spaces"

COMPLEX TERMS (Renewal Options, Termination Rights):
- Extract: Number of options, duration, advance notice required, conditions
- Structure: Free text with all details (e.g., "Two 5-year options with 12 months advance notice")
- Look for: "Option to Renew", "Extension", "Termination", "Early Exit"
- Include: All conditions, rent adjustment methods, deadlines
- Confidence: High (0.9+) only if complete terms extracted

NULL VALUES:
- Use null when: Field not present, unclear, contradictory, or "TBD"
- Always explain: "Not specified in document" or "Contradictory information on pages X and Y"
- Never guess or infer unless explicitly calculable

CITATIONS:
- Page number: Actual page number where found (not PDF page index)
- Quote: Extract 50-200 character quote showing exact source
- Context: Provide enough context to verify extraction
- Multiple pages: If info spans pages, cite primary page

CONFIDENCE SCORING:
- 0.95-1.0: Explicit, unambiguous, in table/schedule
- 0.85-0.94: Clear but requires minor interpretation
- 0.70-0.84: Found but requires calculation or inference
- 0.50-0.69: Ambiguous or unclear wording
- Below 0.50: Very uncertain, consider null instead"""

EXTRACTION_EXAMPLES = """\
=== EXTRACTION EXAMPLES ===

Example 1 - Base Rent Extraction:
Source: "Tenant shall pay annual base rent of Fifteen Thousand Dollars ($15,000.00) per month"
Field: rent.base_rent_monthly
Correct Value: "15000.00"
Reasoning: "Explicitly stated as $15,000.00 per month in rent payment section"
Confidence: 0.98

Example 2 - Square Footage:
Source: "The Premises consist of approximately 3,500 rentable square feet"
Field: property.rentable_area
Correct Value: "3500"
Reasoning: "Explicitly stated as 3,500 RSF in property description"
Confidence: 0.95

Example 3 - Commencement Date:
Source: "Term shall commence on January 15, 2024 (the 'Commencement Date')"
Field: dates.commencement_date
Correct Value: "2024-01-15"
Reasoning: "Explicit commencement date in term section"
Confidence: 0.99

Example 4 - Missing Field:
Source: [No mention of parking in entire document]
Field: other.parking_spaces
Correct Value: null
Reasoning: "Parking is not mentioned or addressed in the lease document"
Confidence: 0.0

Example 5 - Complex Renewal Option:
Source: "Tenant shall have two (2) options to extend the Lease for five (5) years each, exercisable by providing Landlord with twelve (12) months advance written notice"
Field: rights.renewal_options
Correct Value: "Two 5-year options with 12 months advance notice"
Reasoning: "Two renewal options explicitly stated, each for 5-year term with 12-month notice requirement"
Confidence: 0.96

Example 6 - Percentage Extraction:
Source: "Tenant's proportionate share shall be 12.5% of operating expenses"
Field: operating_expenses.tenant_share_percentage
Correct Value: "0.125"
Reasoning: "Tenant's share explicitly stated as 12.5%"
Confidence: 0.98

Example 7 - Execution Date (check signature page!):
Source: "Dated: December 15, 2023" [below Landlord signature]
Field: basic_info.execution_date
Correct Value: "2023-12-15"
Reasoning: "Execution date found on signature page below Landlord signature"
Confidence: 0.98

Example 8 - Tenant Improvement Allowance (check exhibits!):
Source: "Landlord shall provide a tenant improvement allowance of Fifty Thousand Dollars ($50,000.00) as set forth in Exhibit A"
Field: financial.tenant_improvement_allowance
Correct Value: "50000.00"
Reasoning: "TI allowance explicitly stated in Work Letter (Exhibit A)"
Confidence: 0.97

Example 9 - Permitted Use:
Source: "Tenant shall use the Premises solely for general office purposes and for no other use whatsoever"
Field: use.permitted_use
Correct Value: "General office purposes"
Reasoning: "Permitted use explicitly restricted to general office purposes"
Confidence: 0.95

Example 10 - Maintenance Responsibilities:
Source: "Landlord shall maintain the structural elements, roof, and building systems. Tenant shall maintain the interior of the Premises."
Field: maintenance.landlord_responsibilities
Correct Value: "Structural elements, roof, and building systems"
Reasoning: "Landlord responsibilities explicitly listed in Maintenance section"
Confidence: 0.94

Example 11 - Parking (check exhibits/schedules!):
Source: "Tenant shall have the right to use ten (10) unassigned parking spaces in the building parking garage at no additional charge"
Field: other.parking_spaces
Correct Value: "10"
Reasoning: "Parking spaces explicitly stated in Exhibit B (Parking)"
Confidence: 0.96"""

NULL_VALUE_GUIDANCE = """\
=== WHEN TO USE NULL VALUES ===

Use null (not empty string, not "N/A") when:

1. Field not mentioned in document
   - Example: No parking section exists
   - Reasoning: "Parking allocation not addressed in lease"

2. Explicitly TBD or to be determined
   - Example: "Commencement date to be determined"
   - Reasoning: "Commencement date listed as TBD"

3. Contradictory information
   - Example: Page 5 says "$10,000/mo", Page 12 says "$12,000/mo"
   - Reasoning: "Contradictory rent amounts on pages 5 and 12, requires clarification"

4. Ambiguous or unclear
   - Example: "Rent subject to market adjustment"
   - Reasoning: "Base rent not specified, only described as market-based"

5. Document quality issue
   - Example: Critical section is illegible or redacted
   - Reasoning: "Financial terms section illegible in provided PDF"

NEVER:
- Guess values not in document
- Use typical/standard values as defaults
- Infer from other leases or general knowledge
- Leave fields empty without explanation"""


def upgrade():
    # Insert the default prompt template as version 1.1 (active)
    prompt_templates = sa.table(
        'prompt_templates',
        sa.column('version', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('system_prompt', sa.Text),
        sa.column('field_type_guidance', sa.Text),
        sa.column('extraction_examples', sa.Text),
        sa.column('null_value_guidance', sa.Text),
        sa.column('is_active', sa.Boolean),
        sa.column('usage_count', sa.Integer),
        sa.column('created_at', sa.DateTime),
    )

    op.bulk_insert(prompt_templates, [
        {
            'version': '1.1',
            'name': 'Default Extraction Prompt',
            'description': 'Original hardcoded prompt with enhanced field extraction guidance. Seeded from claude_service.py v1.1.',
            'system_prompt': SYSTEM_PROMPT,
            'field_type_guidance': FIELD_TYPE_GUIDANCE,
            'extraction_examples': EXTRACTION_EXAMPLES,
            'null_value_guidance': NULL_VALUE_GUIDANCE,
            'is_active': True,
            'usage_count': 0,
            'created_at': datetime.utcnow(),
        }
    ])


def downgrade():
    op.execute("DELETE FROM prompt_templates WHERE version = '1.1'")
