"""
Generate a sample lease PDF for testing.

This script creates a minimal but realistic lease agreement PDF
that can be used for integration testing.
"""
import fitz  # PyMuPDF
from pathlib import Path


def create_sample_lease_pdf():
    """Create a sample lease PDF with realistic content."""

    # Create a new PDF document
    doc = fitz.open()

    # Page 1: Lease Agreement Header and Basic Terms
    page1 = doc.new_page(width=612, height=792)  # Letter size

    # Define text content for page 1
    page1_text = """
LEASE AGREEMENT

This Lease Agreement ("Lease") is entered into by and between Property Management LLC
("Landlord") and Acme Corporation ("Tenant").

SECTION 1.1 - PREMISES

Landlord hereby leases to Tenant, and Tenant hereby leases from Landlord, those certain
premises located at 789 Office Boulevard, Suite 200, San Francisco, CA 94103. The Premises
consist of approximately five thousand (5,000) rentable square feet on the second floor of
the building known as Tech Center Plaza.

SECTION 2.1 - TERM

The Lease Term shall commence on January 1, 2024 ("Commencement Date") and shall continue
for a period of thirty-six (36) months, ending on December 31, 2026 ("Expiration Date").

SECTION 3.2 - RENEWAL OPTIONS

Tenant shall have two (2) options to extend the Lease Term for additional periods of
twelve (12) months each, provided Tenant is not in default and provides written notice
to Landlord at least one hundred eighty (180) days prior to the Expiration Date.

TENANT INFORMATION:
Name: Acme Corporation
Address: 123 Business Park, Suite 100
City: San Francisco, CA 94105
Contact: John Smith
Email: john.smith@acmecorp.com
Phone: 415-555-0123

LANDLORD INFORMATION:
Name: Property Management LLC
Address: 456 Commercial Plaza
City: San Francisco, CA 94102
Contact: Jane Doe
Email: jane.doe@propertymanagement.com
Phone: 415-555-0456
"""

    # Insert text into page 1
    rect = fitz.Rect(50, 50, 562, 742)
    page1.insert_textbox(rect, page1_text, fontsize=11, align=0)

    # Page 2: Financial Terms
    page2 = doc.new_page(width=612, height=792)

    page2_text = """
SECTION 4.1 - BASE RENT

Tenant shall pay Base Rent of Fifteen Thousand Dollars ($15,000.00) per month, due on
the first day of each calendar month. Base Rent shall increase by three percent (3%)
annually on each anniversary of the Commencement Date.

SECTION 5 - SECURITY DEPOSIT

Upon execution of this Lease, Tenant shall deposit with Landlord the sum of Thirty
Thousand Dollars ($30,000.00) as a security deposit. The security deposit shall be held
by Landlord as security for the faithful performance by Tenant of all terms and
conditions of this Lease.

SECTION 6 - ADDITIONAL RENT

In addition to Base Rent, Tenant shall pay its prorated share of Operating Expenses
including but not limited to common area maintenance, property taxes, and insurance.

SECTION 7 - LATE FEES

If any payment of Rent is not received within five (5) days after the due date, Tenant
shall pay a late charge equal to five percent (5%) of the overdue amount.

PROPERTY DETAILS:
Address: 789 Office Boulevard, Suite 200
City: San Francisco, CA 94103
Square Feet: 5,000
Floor: 2nd Floor
Building: Tech Center Plaza
Type: Office Space
Lease Type: Triple Net (NNN)

FINANCIAL SUMMARY:
Monthly Base Rent: $15,000.00
Annual Escalation: 3%
Security Deposit: $30,000.00
Payment Method: ACH transfer
Late Fee: 5% after 5 days
"""

    rect2 = fitz.Rect(50, 50, 562, 742)
    page2.insert_textbox(rect2, page2_text, fontsize=11, align=0)

    # Page 3: Special Provisions
    page3 = doc.new_page(width=612, height=792)

    page3_text = """
SECTION 8 - PARKING

Landlord shall provide Tenant with ten (10) designated parking spaces in the building's
parking facility at no additional charge. Parking spaces shall be located on Level P1.

SECTION 9 - UTILITIES

Landlord shall provide water and sewer services to the Premises. Tenant shall be
responsible for arranging and paying for electricity, gas, telephone, internet, and
all other utilities required for Tenant's use of the Premises.

SECTION 10 - MAINTENANCE

Landlord shall maintain the exterior of the building, common areas, structural elements,
roof, and building systems. Tenant shall maintain the interior of the Premises including
all fixtures, equipment, and improvements installed by Tenant.

SECTION 11 - IMPROVEMENTS

Landlord shall provide Tenant with a tenant improvement allowance of Fifty Thousand
Dollars ($50,000.00) for build-out of the Premises. Any costs exceeding this allowance
shall be borne by Tenant.

SECTION 12 - SIGNAGE

Tenant shall have the right to install signage in the building directory and one exterior
sign on the building facade, subject to Landlord's approval and compliance with local
zoning regulations.

SECTION 13 - SUBLEASING

Tenant may not sublease all or any portion of the Premises without prior written consent
of Landlord, which consent shall not be unreasonably withheld.

SPECIAL PROVISIONS:
- Parking: 10 spaces included
- Utilities Included: Water and sewer
- Tenant Improvement Allowance: $50,000
- Signage Rights: Building directory + exterior sign
- Subleasing: Allowed with written consent
- Renewal Options: Two 12-month periods
- Notice Period: 180 days for renewal

This Lease constitutes the entire agreement between the parties and supersedes all
prior agreements and understandings.

Executed as of December 15, 2023.

_____________________________          _____________________________
Property Management LLC                Acme Corporation
Landlord                               Tenant
"""

    rect3 = fitz.Rect(50, 50, 562, 742)
    page3.insert_textbox(rect3, page3_text, fontsize=11, align=0)

    # Save the PDF
    output_path = Path(__file__).parent / "sample_lease.pdf"
    doc.save(output_path)
    doc.close()

    print(f"Sample lease PDF created: {output_path}")
    print(f"File size: {output_path.stat().st_size} bytes")
    print(f"Pages: 3")


if __name__ == "__main__":
    create_sample_lease_pdf()
