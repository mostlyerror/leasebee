"""
Unit tests for the Claude API service.

These tests verify Claude API interactions with mocked client,
ensuring no actual API calls or costs are incurred during testing.
"""
import json
import pytest
from unittest.mock import MagicMock

from app.services.claude_service import ClaudeService


@pytest.mark.unit
def test_extract_lease_data_success(mocker, mock_claude_client, mock_extraction_response):
    """
    Test successful lease data extraction with Claude.

    Verifies:
    - Claude API called with correct parameters
    - PDF properly encoded to base64
    - Response properly parsed
    - Metadata calculated correctly (tokens, cost, timing)
    """
    service = ClaudeService()

    # Test PDF bytes
    pdf_bytes = b"%PDF-1.4\ntest content"

    # Extract data
    result = service.extract_lease_data(pdf_bytes)

    # Verify API was called
    mock_claude_client.messages.create.assert_called_once()
    call_kwargs = mock_claude_client.messages.create.call_args[1]

    # Verify model and max_tokens
    assert call_kwargs['model'] == service.model
    assert call_kwargs['max_tokens'] == 8000

    # Verify message structure
    messages = call_kwargs['messages']
    assert len(messages) == 1
    assert messages[0]['role'] == 'user'
    assert len(messages[0]['content']) == 2

    # Verify PDF document in message
    doc_content = messages[0]['content'][0]
    assert doc_content['type'] == 'document'
    assert doc_content['source']['type'] == 'base64'
    assert doc_content['source']['media_type'] == 'application/pdf'
    assert 'data' in doc_content['source']

    # Verify prompt text in message
    text_content = messages[0]['content'][1]
    assert text_content['type'] == 'text'
    assert 'lease abstraction expert' in text_content['text'].lower()

    # Verify result structure
    assert 'extractions' in result
    assert 'reasoning' in result
    assert 'citations' in result
    assert 'confidence' in result
    assert 'metadata' in result

    # Verify metadata
    metadata = result['metadata']
    assert metadata['model_version'] == service.model
    assert metadata['prompt_version'] == "1.0"
    assert metadata['input_tokens'] == 5000
    assert metadata['output_tokens'] == 2000
    assert metadata['total_cost'] > 0
    assert metadata['processing_time_seconds'] >= 0

    # Verify extracted data matches mock
    assert result['extractions']['tenant.name'] == "Acme Corporation"
    assert result['extractions']['financial.base_rent'] == "15000.00"


@pytest.mark.unit
def test_extract_lease_data_with_few_shot_examples(mocker, mock_claude_client, mock_extraction_response):
    """
    Test extraction with few-shot examples included in prompt.

    Verifies that few-shot examples are properly incorporated
    into the prompt for improved extraction accuracy.
    """
    service = ClaudeService()

    # Create few-shot examples
    examples = [
        {
            'field_path': 'tenant.name',
            'source_text': 'Agreement between ABC Corp and XYZ Landlord',
            'correct_value': 'ABC Corp',
            'reasoning': 'Tenant is the first party mentioned after "between"'
        },
        {
            'field_path': 'financial.base_rent',
            'source_text': 'Monthly rent of $5,000',
            'correct_value': '5000.00',
            'reasoning': 'Explicit monthly rent amount'
        }
    ]

    pdf_bytes = b"%PDF-1.4\ntest"

    # Extract with examples
    result = service.extract_lease_data(pdf_bytes, few_shot_examples=examples)

    # Verify examples were included in prompt
    call_kwargs = mock_claude_client.messages.create.call_args[1]
    prompt = call_kwargs['messages'][0]['content'][1]['text']

    assert 'EXAMPLES OF CORRECT EXTRACTIONS' in prompt
    assert 'ABC Corp' in prompt
    assert 'Monthly rent of $5,000' in prompt

    # Verify extraction still works
    assert 'extractions' in result


@pytest.mark.unit
def test_extract_lease_data_api_error(mocker, mock_claude_client):
    """
    Test handling of Claude API errors.

    Verifies that API exceptions are caught and re-raised
    with descriptive messages.
    """
    # Make API call raise an error
    mock_claude_client.messages.create.side_effect = Exception("API connection error")

    service = ClaudeService()
    pdf_bytes = b"%PDF-1.4\ntest"

    # Verify exception is raised with descriptive message
    with pytest.raises(Exception) as exc_info:
        service.extract_lease_data(pdf_bytes)

    assert "Claude API error" in str(exc_info.value)
    assert "API connection error" in str(exc_info.value)


@pytest.mark.unit
def test_parse_response_success(mocker):
    """
    Test successful parsing of Claude's JSON response.

    Verifies that well-formed JSON responses are properly parsed.
    """
    service = ClaudeService()

    # Create mock response
    response_data = {
        "extractions": {"tenant.name": "Test Corp"},
        "reasoning": {"tenant.name": "Found in header"},
        "citations": {"tenant.name": {"page": 1, "quote": "Test Corp"}},
        "confidence": {"tenant.name": 0.95}
    }

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(response_data))]

    # Parse response
    result = service._parse_response(mock_response)

    # Verify parsing
    assert result['extractions']['tenant.name'] == "Test Corp"
    assert result['reasoning']['tenant.name'] == "Found in header"
    assert result['confidence']['tenant.name'] == 0.95


@pytest.mark.unit
def test_parse_response_with_extra_text(mocker):
    """
    Test parsing Claude responses that include extra text around JSON.

    Sometimes Claude adds explanatory text before/after the JSON.
    The parser should extract just the JSON object.
    """
    service = ClaudeService()

    # Response with extra text
    response_text = """Here is the extracted data:

{
  "extractions": {"tenant.name": "Test Corp"},
  "reasoning": {"tenant.name": "Found in header"},
  "citations": {},
  "confidence": {}
}

I hope this helps!"""

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]

    # Parse response
    result = service._parse_response(mock_response)

    # Verify parsing still works
    assert result['extractions']['tenant.name'] == "Test Corp"


@pytest.mark.unit
def test_parse_response_missing_keys(mocker):
    """
    Test that missing keys in response are handled gracefully.

    If Claude omits some keys (reasoning, citations, etc.),
    they should be initialized as empty dicts.
    """
    service = ClaudeService()

    # Minimal response with only extractions
    response_data = {
        "extractions": {"tenant.name": "Test Corp"}
    }

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(response_data))]

    # Parse response
    result = service._parse_response(mock_response)

    # Verify missing keys are initialized
    assert 'extractions' in result
    assert 'reasoning' in result
    assert 'citations' in result
    assert 'confidence' in result

    # Verify missing keys are empty dicts
    assert result['reasoning'] == {}
    assert result['citations'] == {}
    assert result['confidence'] == {}


@pytest.mark.unit
def test_parse_response_invalid_json(mocker):
    """
    Test handling of invalid JSON responses.

    Verifies that malformed JSON raises appropriate exceptions.
    """
    service = ClaudeService()

    # Invalid JSON
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is not valid JSON {incomplete")]

    # Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        service._parse_response(mock_response)

    assert "Failed to parse Claude response" in str(exc_info.value)


@pytest.mark.unit
def test_parse_response_no_json(mocker):
    """
    Test handling of responses with no JSON object.
    """
    service = ClaudeService()

    # No JSON in response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Sorry, I could not extract data from this document.")]

    # Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        service._parse_response(mock_response)

    assert "No JSON object found" in str(exc_info.value)


@pytest.mark.unit
def test_calculate_cost_accuracy():
    """
    Test cost calculation accuracy.

    Claude 3.5 Sonnet pricing (as of Jan 2025):
    - Input: $3 per million tokens
    - Output: $15 per million tokens
    """
    service = ClaudeService()

    # Test case 1: 1 million input, 1 million output
    cost = service._calculate_cost(1_000_000, 1_000_000)
    assert cost == 18.0  # $3 + $15

    # Test case 2: 5000 input, 2000 output
    cost = service._calculate_cost(5000, 2000)
    expected = (5000 / 1_000_000) * 3.0 + (2000 / 1_000_000) * 15.0
    assert cost == round(expected, 4)

    # Test case 3: Zero tokens
    cost = service._calculate_cost(0, 0)
    assert cost == 0.0

    # Test case 4: Large numbers
    cost = service._calculate_cost(100_000, 50_000)
    expected = (100_000 / 1_000_000) * 3.0 + (50_000 / 1_000_000) * 15.0
    assert cost == round(expected, 4)
    assert cost == 1.05  # $0.30 + $0.75


@pytest.mark.unit
def test_calculate_cost_rounding():
    """
    Test that cost is properly rounded to 4 decimal places.
    """
    service = ClaudeService()

    # Use numbers that would produce many decimal places
    cost = service._calculate_cost(1234, 5678)

    # Verify it's rounded to 4 decimal places
    assert isinstance(cost, float)
    assert len(str(cost).split('.')[-1]) <= 4


@pytest.mark.unit
def test_build_extraction_prompt_structure():
    """
    Test that the extraction prompt has the correct structure.

    Verifies:
    - Instructions are clear
    - Field schema is included
    - JSON structure is specified
    """
    service = ClaudeService()

    prompt = service._build_extraction_prompt()

    # Verify key components are present
    assert "lease abstraction expert" in prompt.lower()
    assert "Extract structured information" in prompt
    assert "FIELD SCHEMA" in prompt
    assert "JSON" in prompt
    assert "extractions" in prompt
    assert "reasoning" in prompt
    assert "citations" in prompt
    assert "confidence" in prompt

    # Verify instructions
    assert "Return ONLY valid JSON" in prompt
    assert "Do not include any text before or after" in prompt


@pytest.mark.unit
def test_build_extraction_prompt_with_examples():
    """
    Test prompt building with few-shot examples.
    """
    service = ClaudeService()

    examples = [
        {
            'field_path': 'tenant.name',
            'source_text': 'Lease with ABC Corp',
            'correct_value': 'ABC Corp',
            'reasoning': 'Explicitly named as tenant'
        }
    ]

    prompt = service._build_extraction_prompt(few_shot_examples=examples)

    # Verify examples are included
    assert "EXAMPLES OF CORRECT EXTRACTIONS" in prompt
    assert "tenant.name" in prompt
    assert "ABC Corp" in prompt
    assert "Explicitly named as tenant" in prompt


@pytest.mark.unit
def test_claude_service_singleton():
    """
    Test that claude_service is properly initialized as a singleton.
    """
    from app.services.claude_service import claude_service

    assert claude_service is not None
    assert isinstance(claude_service, ClaudeService)
    assert hasattr(claude_service, 'client')
    assert hasattr(claude_service, 'model')
    assert hasattr(claude_service, 'prompt_version')


@pytest.mark.unit
def test_prompt_version_tracking(mocker, mock_claude_client, mock_extraction_response):
    """
    Test that prompt version is tracked for learning purposes.
    """
    service = ClaudeService()

    assert service.prompt_version == "1.0"

    # Verify it's included in metadata
    pdf_bytes = b"%PDF-1.4\ntest"
    result = service.extract_lease_data(pdf_bytes)

    assert result['metadata']['prompt_version'] == "1.0"


@pytest.mark.unit
def test_extraction_timing(mocker, mock_claude_client, mock_extraction_response):
    """
    Test that processing time is accurately measured.
    """
    service = ClaudeService()

    pdf_bytes = b"%PDF-1.4\ntest"
    result = service.extract_lease_data(pdf_bytes)

    # Verify timing is recorded
    assert 'processing_time_seconds' in result['metadata']
    assert result['metadata']['processing_time_seconds'] >= 0
    assert isinstance(result['metadata']['processing_time_seconds'], float)
