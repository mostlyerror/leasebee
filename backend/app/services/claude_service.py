"""Claude API service for lease extraction."""
import time
import json
import base64
from typing import Dict, Any, Optional
from anthropic import Anthropic

from app.core.config import settings
from app.schemas.field_schema import get_schema_for_claude, get_field_paths


class ClaudeService:
    """Service for interacting with Claude API for lease extraction."""

    def __init__(self):
        """Initialize Anthropic client."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.prompt_version = "1.0"  # Track prompt versions for learning

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
