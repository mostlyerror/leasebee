"""
Validation service for extracted field values.

This service validates and normalizes extracted values, checking for:
- Format correctness (dates, currency, numbers)
- Range validation
- Cross-field consistency
- Type conformance
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import re
from decimal import Decimal, InvalidOperation


class ValidationResult:
    """Result of validation with normalized value and warnings."""

    def __init__(
        self,
        value: Any,
        warnings: Optional[List[str]] = None,
        confidence_adjustment: float = 0.0
    ):
        """
        Initialize validation result.

        Args:
            value: Normalized value
            warnings: List of validation warnings
            confidence_adjustment: Adjustment to confidence score (+/- 0.2 max)
        """
        self.value = value
        self.warnings = warnings or []
        self.confidence_adjustment = max(-0.2, min(0.2, confidence_adjustment))


class ValidationService:
    """Validates and normalizes extracted field values."""

    def validate_and_normalize(
        self,
        field_path: str,
        value: Any,
        field_type: str,
        all_extractions: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Validate and normalize a field value.

        Args:
            field_path: Field path (e.g., "dates.commencement_date")
            value: Extracted value to validate
            field_type: Field type from schema (DATE, CURRENCY, NUMBER, etc.)
            all_extractions: All extracted values for cross-field validation

        Returns:
            ValidationResult with normalized value, warnings, and confidence adjustment
        """
        if value is None:
            return ValidationResult(None)

        # Route to appropriate validator based on field type
        validators = {
            'date': self.validate_date,
            'currency': self.validate_currency,
            'number': self.validate_number,
            'percentage': self.validate_percentage,
            'area': self.validate_area,
            'boolean': self.validate_boolean,
            'address': self.validate_address,
            'text': self.validate_text,
        }

        # Normalize field type to lowercase
        field_type_lower = field_type.lower()
        validator = validators.get(field_type_lower, self.validate_text)

        # Perform field-specific validation
        result = validator(value, field_path)

        # Cross-field consistency checks if all extractions provided
        if all_extractions and result.value is not None:
            consistency_warnings = self.check_consistency(
                field_path,
                result.value,
                all_extractions
            )
            result.warnings.extend(consistency_warnings)

            # Adjust confidence if consistency issues found
            if consistency_warnings:
                result.confidence_adjustment -= 0.1

        return result

    def validate_date(self, value: str, field_path: str) -> ValidationResult:
        """
        Validate and normalize date to ISO format (YYYY-MM-DD).

        Args:
            value: Date value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized date
        """
        warnings = []

        # Convert to string if not already
        value_str = str(value).strip()

        # Already in ISO format?
        if re.match(r'^\d{4}-\d{2}-\d{2}$', value_str):
            try:
                datetime.strptime(value_str, '%Y-%m-%d')
                return ValidationResult(value_str, warnings)
            except ValueError:
                warnings.append(f"Invalid date format: {value_str}")
                return ValidationResult(None, warnings, -0.2)

        # Try to parse various formats
        formats = [
            '%m/%d/%Y', '%m/%d/%y',  # US format: 01/15/2024, 1/15/24
            '%d/%m/%Y', '%d/%m/%y',  # International: 15/01/2024
            '%B %d, %Y',              # January 15, 2024
            '%b %d, %Y',              # Jan 15, 2024
            '%Y/%m/%d',               # ISO with slashes: 2024/01/15
            '%m-%d-%Y',               # US with dashes: 01-15-2024
            '%Y%m%d',                 # Compact: 20240115
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value_str, fmt)
                normalized = dt.strftime('%Y-%m-%d')
                warnings.append(f"Date format normalized from '{value_str}' to '{normalized}'")
                return ValidationResult(normalized, warnings, 0.0)
            except ValueError:
                continue

        # Could not parse
        warnings.append(f"Could not parse date: {value_str}")
        return ValidationResult(value_str, warnings, -0.2)

    def validate_currency(self, value: Any, field_path: str) -> ValidationResult:
        """
        Validate and normalize currency values.

        Args:
            value: Currency value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized currency (numeric, 2 decimals)
        """
        warnings = []

        # Convert to string for processing
        value_str = str(value).strip()

        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,€£¥]', '', value_str)

        try:
            # Convert to Decimal for precision
            amount = Decimal(cleaned)

            # Round to 2 decimal places
            normalized = float(round(amount, 2))

            # Sanity checks
            if normalized < 0:
                warnings.append(f"Negative currency value: {normalized}")
                # Don't adjust confidence - negative might be valid (credits)

            if normalized > 100_000_000:  # $100M
                warnings.append(f"Unusually large currency value: ${normalized:,.2f}")

            if value_str != str(normalized):
                warnings.append(f"Currency normalized from '{value_str}' to '{normalized}'")

            return ValidationResult(normalized, warnings)

        except (ValueError, TypeError, InvalidOperation):
            warnings.append(f"Could not parse currency: {value}")
            return ValidationResult(value, warnings, -0.2)

    def validate_number(self, value: Any, field_path: str) -> ValidationResult:
        """
        Validate numeric fields.

        Args:
            value: Numeric value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized number
        """
        warnings = []

        try:
            # Remove commas and convert
            cleaned = str(value).replace(',', '').strip()
            num = float(cleaned)

            # Check for reasonable ranges based on field name
            if 'month' in field_path.lower():
                if num < 0 or num > 1200:  # 100 years in months
                    warnings.append(f"Unusual month value: {num}")

            if value != num:
                warnings.append(f"Number normalized from '{value}' to '{num}'")

            return ValidationResult(num, warnings)

        except (ValueError, TypeError):
            warnings.append(f"Could not parse number: {value}")
            return ValidationResult(value, warnings, -0.2)

    def validate_percentage(self, value: Any, field_path: str) -> ValidationResult:
        """
        Validate percentage (should be decimal 0-1).

        Args:
            value: Percentage value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized percentage (as decimal)
        """
        warnings = []

        try:
            # Remove % symbol if present
            value_str = str(value).replace('%', '').strip()
            pct = float(value_str)

            # If given as percentage (>1), convert to decimal
            if pct > 1:
                pct = pct / 100
                warnings.append(f"Percentage converted from {value} to {pct}")

            # Validate range
            if pct < 0 or pct > 1:
                warnings.append(f"Percentage {pct} outside valid range [0, 1]")

            return ValidationResult(round(pct, 4), warnings)

        except (ValueError, TypeError):
            warnings.append(f"Could not parse percentage: {value}")
            return ValidationResult(value, warnings, -0.2)

    def validate_area(self, value: Any, field_path: str) -> ValidationResult:
        """
        Validate area/square footage.

        Args:
            value: Area value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized area (numeric)
        """
        warnings = []

        # Remove "SF", "square feet", etc
        value_str = str(value)
        cleaned = re.sub(r'(?i)\s*(sf|square\s+feet|sq\.?\s*ft\.?|rsf|usf)', '', value_str)
        cleaned = cleaned.replace(',', '').strip()

        try:
            area = float(cleaned)

            # Sanity checks
            if area < 1:
                warnings.append(f"Very small area: {area} SF")
            elif area > 10_000_000:  # 10 million SF
                warnings.append(f"Very large area: {area:,.0f} SF")

            if 'rentable' in field_path.lower():
                if area < 10:
                    warnings.append("Rentable area suspiciously small")
            elif 'usable' in field_path.lower():
                if area < 10:
                    warnings.append("Usable area suspiciously small")

            if str(value) != str(area):
                warnings.append(f"Area normalized from '{value}' to '{area}'")

            return ValidationResult(area, warnings)

        except (ValueError, TypeError):
            warnings.append(f"Could not parse area: {value}")
            return ValidationResult(value, warnings, -0.2)

    def validate_boolean(self, value: Any, field_path: str) -> ValidationResult:
        """
        Validate boolean fields.

        Args:
            value: Boolean value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized boolean
        """
        warnings = []

        # Convert various representations to bool
        true_values = {'true', 't', 'yes', 'y', '1', 'True', True, 1}
        false_values = {'false', 'f', 'no', 'n', '0', 'False', False, 0}

        if value in true_values:
            return ValidationResult(True, warnings)
        elif value in false_values:
            return ValidationResult(False, warnings)
        else:
            warnings.append(f"Could not parse boolean: {value}")
            return ValidationResult(None, warnings, -0.2)

    def validate_address(self, value: str, field_path: str) -> ValidationResult:
        """
        Validate address format.

        Args:
            value: Address value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized address
        """
        warnings = []

        value_str = str(value).strip()

        # Check for suite/unit in main address (should be separate)
        suite_pattern = r'(?i)(suite|ste\.?|unit|#)\s*[\w\d-]+'
        if re.search(suite_pattern, value_str):
            if 'suite' not in field_path.lower():
                warnings.append("Suite/unit found in address - consider extracting separately")

        # Check for basic address components
        has_number = bool(re.search(r'\b\d+\b', value_str))
        has_state = bool(re.search(r'\b[A-Z]{2}\b', value_str))
        has_zip = bool(re.search(r'\b\d{5}(-\d{4})?\b', value_str))

        if not has_number:
            warnings.append("Address missing street number")
        if not has_state:
            warnings.append("Address missing state abbreviation")
        if not has_zip:
            warnings.append("Address missing ZIP code")

        return ValidationResult(value_str, warnings)

    def validate_text(self, value: Any, field_path: str) -> ValidationResult:
        """
        Basic text validation.

        Args:
            value: Text value to validate
            field_path: Field path for context

        Returns:
            ValidationResult with normalized text
        """
        warnings = []
        text = str(value).strip()

        # Check for suspiciously short values
        if len(text) < 2 and 'name' in field_path.lower():
            warnings.append(f"Suspiciously short {field_path}: '{text}'")

        return ValidationResult(text, warnings)

    def check_consistency(
        self,
        field_path: str,
        value: Any,
        all_extractions: Dict[str, Any]
    ) -> List[str]:
        """
        Check cross-field consistency.

        Args:
            field_path: Field being validated
            value: Validated value
            all_extractions: All extracted field values

        Returns:
            List of consistency warnings
        """
        warnings = []

        # Date range checks
        if field_path == 'dates.expiration_date' and value:
            comm_date = all_extractions.get('dates.commencement_date')
            if comm_date:
                try:
                    exp = datetime.strptime(str(value), '%Y-%m-%d')
                    comm = datetime.strptime(str(comm_date), '%Y-%m-%d')
                    if exp <= comm:
                        warnings.append("Expiration date should be after commencement date")
                except ValueError:
                    pass

        # Annual vs monthly rent consistency
        if field_path == 'rent.base_rent_annual' and value:
            monthly = all_extractions.get('rent.base_rent_monthly')
            if monthly:
                try:
                    expected_annual = float(monthly) * 12
                    actual_annual = float(value)
                    diff_pct = abs(actual_annual - expected_annual) / expected_annual
                    if diff_pct > 0.05:  # More than 5% difference
                        warnings.append(
                            f"Annual rent ${actual_annual:,.2f} doesn't match "
                            f"monthly ${float(monthly):,.2f} × 12 = ${expected_annual:,.2f}"
                        )
                except (ValueError, TypeError, ZeroDivisionError):
                    pass

        # Rent per SF calculation
        if field_path == 'rent.rent_per_sf_annual' and value:
            annual_rent = all_extractions.get('rent.base_rent_annual')
            sf = all_extractions.get('property.rentable_area')
            if annual_rent and sf:
                try:
                    expected = float(annual_rent) / float(sf)
                    actual = float(value)
                    diff_pct = abs(actual - expected) / expected if expected > 0 else 0
                    if diff_pct > 0.05:  # More than 5% difference
                        warnings.append(
                            f"Rent/SF ${actual:.2f} doesn't match "
                            f"annual rent / SF: ${expected:.2f}"
                        )
                except (ValueError, TypeError, ZeroDivisionError):
                    pass

        # Usable vs Rentable area (usable should be <= rentable)
        if field_path == 'property.usable_area' and value:
            rentable = all_extractions.get('property.rentable_area')
            if rentable:
                try:
                    if float(value) > float(rentable):
                        warnings.append(
                            f"Usable area ({value}) greater than rentable area ({rentable})"
                        )
                except (ValueError, TypeError):
                    pass

        # Lease term calculation
        if field_path == 'dates.lease_term_months' and value:
            comm = all_extractions.get('dates.commencement_date')
            exp = all_extractions.get('dates.expiration_date')
            if comm and exp:
                try:
                    comm_dt = datetime.strptime(str(comm), '%Y-%m-%d')
                    exp_dt = datetime.strptime(str(exp), '%Y-%m-%d')
                    delta = exp_dt - comm_dt
                    calculated_months = delta.days / 30.44  # Average days per month
                    stated_months = float(value)
                    diff = abs(calculated_months - stated_months)
                    if diff > 1:  # More than 1 month difference
                        warnings.append(
                            f"Stated term ({stated_months} months) differs from calculated "
                            f"term ({calculated_months:.1f} months) based on dates"
                        )
                except (ValueError, TypeError):
                    pass

        return warnings


# Singleton instance
validation_service = ValidationService()
