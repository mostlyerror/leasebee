"""Claude API service for lease extraction."""
import time
import json
import base64
from typing import Dict, Any, Optional, List
from anthropic import Anthropic

from app.core.config import settings
from app.schemas.field_schema import get_schema_for_claude, get_field_paths, get_field_by_path


class ClaudeService:
    """Service for interacting with Claude API for lease extraction."""

    def __init__(self):
        """Initialize Anthropic client."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.prompt_version = "1.1"  # Enhanced field extraction guidance

    def extract_lease_data(
        self,
        pdf_bytes: bytes,
        few_shot_examples: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from a lease PDF using Claude.

        Args:
            pdf_bytes: PDF file content as bytes
            few_shot_examples: Optional list of example extractions for few-shot learning

        Returns:
            Dictionary with:
            - extractions: Extracted field values
            - reasoning: Explanation for each field
            - citations: Source locations for each field
            - confidence: Confidence scores for each field
            - metadata: Token usage and timing info
        """
        start_time = time.time()

        # Build the prompt
        prompt = self._build_extraction_prompt(few_shot_examples)

        try:
            # Encode PDF to base64
            pdf_base64 = base64.standard_b64encode(pdf_bytes).decode('utf-8')

            # Call Claude API with PDF
            # Note: Using the beta PDF feature
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            }
                        ],
                    }
                ],
            )

            # Parse response
            result = self._parse_response(response)

            # Add metadata
            processing_time = time.time() - start_time
            result['metadata'] = {
                'model_version': self.model,
                'prompt_version': self.prompt_version,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_cost': self._calculate_cost(
                    response.usage.input_tokens,
                    response.usage.output_tokens
                ),
                'processing_time_seconds': processing_time,
            }

            return result

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

    def extract_lease_data_with_refinement(
        self,
        pdf_bytes: bytes,
        confidence_threshold: float = 0.70,
        few_shot_examples: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Extract with multi-pass refinement for low-confidence fields.

        Strategy:
        1. Initial extraction of all fields
        2. Identify low-confidence fields (< threshold)
        3. Re-extract those fields with focused prompt
        4. Merge results, preferring higher confidence

        Args:
            pdf_bytes: PDF file content as bytes
            confidence_threshold: Threshold below which to re-extract (default 0.70)
            few_shot_examples: Optional examples for few-shot learning

        Returns:
            Dictionary with merged extraction results and metadata
        """
        # Pass 1: Extract all fields
        initial_result = self.extract_lease_data(pdf_bytes, few_shot_examples)

        # Identify low-confidence fields
        low_confidence_fields = [
            field_path
            for field_path, confidence in initial_result['confidence'].items()
            if confidence < confidence_threshold and initial_result['extractions'].get(field_path) is not None
        ]

        # If no low-confidence fields, return initial result
        if not low_confidence_fields:
            initial_result['metadata']['multi_pass'] = False
            initial_result['metadata']['refined_fields'] = []
            return initial_result

        # Pass 2: Re-extract low-confidence fields with focused prompt
        focused_result = self._extract_focused_fields(
            pdf_bytes,
            low_confidence_fields,
            initial_context=initial_result['extractions']
        )

        # Merge results - prefer focused extraction if confidence improved
        merged_result = self._merge_extraction_results(
            initial_result,
            focused_result,
            low_confidence_fields
        )

        merged_result['metadata']['multi_pass'] = True
        merged_result['metadata']['refined_fields'] = low_confidence_fields

        return merged_result

    def _extract_focused_fields(
        self,
        pdf_bytes: bytes,
        field_paths: List[str],
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract specific fields with a focused prompt.

        This targeted extraction provides:
        - Field-specific guidance
        - Context from other extracted values
        - More detailed instructions

        Args:
            pdf_bytes: PDF file content as bytes
            field_paths: List of field paths to re-extract
            initial_context: Previously extracted values for context

        Returns:
            Extraction result for focused fields
        """
        # Build field-specific descriptions
        fields_description = []
        for path in field_paths:
            field_def = get_field_by_path(path)
            if field_def:
                fields_description.append(
                    f"- {path}: {field_def['description']} (Type: {field_def['type'].value})"
                )

        fields_text = "\n".join(fields_description)

        # Build context information (fields already extracted with confidence)
        context_info = []
        for k, v in initial_context.items():
            if k not in field_paths and v is not None:
                context_info.append(f"- {k}: {v}")

        context_text = "\n".join(context_info) if context_info else "None available"

        # Build focused prompt
        focused_prompt = f"""You are a commercial lease abstraction expert performing a FOCUSED RE-EXTRACTION.

CONTEXT FROM INITIAL EXTRACTION:
The following fields have already been extracted with acceptable confidence:
{context_text}

FIELDS TO RE-EXTRACT:
These fields had low confidence in the initial extraction and need careful re-examination:
{fields_text}

INSTRUCTIONS:
1. CAREFULLY re-read the document focusing ONLY on these specific fields
2. Use the context from other extracted fields to help locate information
3. Look in multiple locations: table of contents, specific sections, exhibits, schedules
4. Cross-reference information across different parts of the document
5. If truly not present after thorough search, confidently set to null with clear reasoning
6. Provide very specific citations with exact page number and direct quote

Return ONLY valid JSON with this structure:
{{
  "extractions": {{"field_path": "value"}},
  "reasoning": {{"field_path": "detailed reasoning explaining where and how you found this"}},
  "citations": {{"field_path": {{"page": N, "quote": "exact text from document"}}}},
  "confidence": {{"field_path": 0.0-1.0}}
}}

{self._get_field_type_guidance()}

Now perform the focused re-extraction. Return ONLY the JSON object, no other text."""

        try:
            # Encode PDF to base64
            pdf_base64 = base64.standard_b64encode(pdf_bytes).decode('utf-8')

            # Call Claude API with focused prompt
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,  # Smaller response for focused extraction
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": focused_prompt,
                            }
                        ],
                    }
                ],
            )

            # Parse response
            result = self._parse_response(response)

            # Add metadata about this focused extraction
            result['metadata'] = {
                'model_version': self.model,
                'prompt_version': f"{self.prompt_version}_focused",
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_cost': self._calculate_cost(
                    response.usage.input_tokens,
                    response.usage.output_tokens
                ),
                'fields_refined': field_paths
            }

            return result

        except Exception as e:
            raise Exception(f"Focused extraction error: {str(e)}")

    def _merge_extraction_results(
        self,
        initial: Dict[str, Any],
        focused: Dict[str, Any],
        refined_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Merge initial and focused extraction results.

        Strategy:
        - Use focused result if confidence improved by >= 0.10
        - Otherwise keep initial result
        - Track which fields were updated

        Args:
            initial: Initial extraction result
            focused: Focused extraction result
            refined_fields: List of fields that were re-extracted

        Returns:
            Merged extraction result
        """
        merged = initial.copy()
        updated_fields = []
        improvements = {}

        for field_path in refined_fields:
            initial_conf = initial['confidence'].get(field_path, 0.0)
            focused_conf = focused['confidence'].get(field_path, 0.0)

            # Use focused extraction if confidence improved significantly
            confidence_gain = focused_conf - initial_conf

            if confidence_gain >= 0.10:
                # Update with focused extraction
                merged['extractions'][field_path] = focused['extractions'].get(field_path)
                merged['reasoning'][field_path] = focused['reasoning'].get(field_path)
                merged['citations'][field_path] = focused['citations'].get(field_path)
                merged['confidence'][field_path] = focused_conf

                updated_fields.append(field_path)
                improvements[field_path] = {
                    'initial_confidence': initial_conf,
                    'focused_confidence': focused_conf,
                    'improvement': confidence_gain
                }

        # Update metadata with merge information
        merged['metadata']['updated_from_refinement'] = updated_fields
        merged['metadata']['refinement_improvements'] = improvements

        # Add costs from both passes
        if 'total_cost' in focused['metadata']:
            merged['metadata']['total_cost'] += focused['metadata']['total_cost']
            merged['metadata']['initial_cost'] = initial['metadata']['total_cost']
            merged['metadata']['refinement_cost'] = focused['metadata']['total_cost']

        return merged

    def _build_extraction_prompt(self, few_shot_examples: Optional[list] = None) -> str:
        """
        Build the extraction prompt for Claude.

        Args:
            few_shot_examples: Optional examples for few-shot learning

        Returns:
            Complete prompt string
        """
        # Get field schema
        schema = get_schema_for_claude()
        field_paths = get_field_paths()

        prompt = f"""You are a commercial lease abstraction expert. Extract structured information from this lease PDF.

For each field in the schema below:
1. Extract the exact value from the document
2. Explain your reasoning - why did you extract this specific value?
3. Cite the specific section (page number and brief quote) where you found it
4. Rate your confidence (0.0-1.0) based on how clear the information is

If a field is not present or cannot be determined from the document, set the value to null and explain why in the reasoning.

CRITICAL: Return ONLY valid JSON. Do not include any text before or after the JSON object.

Return a JSON object with this EXACT structure:
{{
  "extractions": {{"field_path": "value"}},
  "reasoning": {{"field_path": "explanation"}},
  "citations": {{"field_path": {{"page": number, "quote": "brief relevant quote"}}}},
  "confidence": {{"field_path": 0.95}}
}}

FIELD SCHEMA:
{schema}

{self._get_field_type_guidance()}

{self._get_extraction_examples()}

{self._get_null_value_guidance()}

"""

        # Add few-shot examples if provided (for Phase 3)
        if few_shot_examples:
            prompt += "\n\nEXAMPLES OF CORRECT EXTRACTIONS:\n\n"
            for example in few_shot_examples:
                prompt += f"Field: {example['field_path']}\n"
                prompt += f"Source: {example['source_text']}\n"
                prompt += f"Correct Value: {example['correct_value']}\n"
                prompt += f"Reasoning: {example['reasoning']}\n\n"

        prompt += "\n\nNow extract data from the provided lease document. Return ONLY the JSON object, no other text."

        return prompt

    def _parse_response(self, response) -> Dict[str, Any]:
        """
        Parse Claude's response into structured format.

        Args:
            response: Anthropic API response object

        Returns:
            Parsed extraction data
        """
        try:
            # Get the text content
            content = response.content[0].text

            # Find JSON in the response (Claude sometimes adds explanation text)
            # Look for the first { and last }
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")

            json_str = content[start_idx:end_idx]

            # Parse JSON
            data = json.loads(json_str)

            # Validate structure
            required_keys = ['extractions', 'reasoning', 'citations', 'confidence']
            for key in required_keys:
                if key not in data:
                    data[key] = {}

            return data

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Claude response as JSON: {str(e)}\nResponse: {content}")
        except Exception as e:
            raise Exception(f"Failed to parse Claude response: {str(e)}")

    def _get_field_type_guidance(self) -> str:
        """Get comprehensive field-type specific extraction guidance."""
        return """
=== CRITICAL EXTRACTION GUIDELINES ===

EXECUTION DATE (basic_info.execution_date):
-- CRITICAL: Check signature blocks at the end of the document
-- Look for: "Dated:", "Executed:", "Date Signed:" near signatures
-- Common locations: Last page, signature page, execution clause
-- Format: YYYY-MM-DD (convert from "December 15, 2023" → "2023-12-15")
-- If different dates for landlord/tenant, use the later date
-- If "as of" date precedes signatures, that's the execution date

DATES:
- Format: Always return ISO format YYYY-MM-DD
- Common locations: Look in "Term", "Lease Period", or first page summary
- Handle variations: "January 1, 2024" → "2024-01-01", "1/1/24" → "2024-01-01"
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
- Variations: "5,000 SF" → "5000", "Five thousand square feet" → "5000"
- Confidence: High (0.95+) if explicitly stated, Medium (0.7-0.9) if calculated from rent/SF

ADDRESSES:
- Format: Full street address with city, state, ZIP
- Suite/unit: Extract separately to suite_unit field, not in main address
- Look for: First page, "Premises", "Property Description"
- Example: "123 Main St, Suite 200, San Francisco, CA 94105"
  → property.address: "123 Main St, San Francisco, CA 94105"
  → property.suite_unit: "Suite 200"
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
- Context: "5% annual increase" → "0.05", "Tenant's 12.5% share" → "0.125"
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
- Below 0.50: Very uncertain, consider null instead
"""

    def _get_extraction_examples(self) -> str:
        """Get concrete extraction examples for each field type."""
        return """
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
Confidence: 0.96
"""

    def _get_null_value_guidance(self) -> str:
        """Get guidance on when to use null values."""
        return """
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
- Leave fields empty without explanation
"""

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API cost based on token usage.

        Claude 3.5 Sonnet pricing (as of Jan 2025):
        - Input: $3 per million tokens
        - Output: $15 per million tokens

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * 3.0
        output_cost = (output_tokens / 1_000_000) * 15.0
        return round(input_cost + output_cost, 4)


# Singleton instance
claude_service = ClaudeService()
