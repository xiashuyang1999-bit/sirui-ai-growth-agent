"""Tests for local B2B inquiry qualification."""

import unittest

from agents.inquiry_agent import qualify_inquiry


class InquiryAgentTests(unittest.TestCase):
    def test_verified_complete_b2b_inquiry_is_grade_a(self) -> None:
        inquiry = {
            "source": "website_form",
            "company": "Example Distribution Ltd",
            "website": "https://example.com",
            "company_verified": True,
            "contact_name": "Alex",
            "email": "alex@example.com",
            "country": "United Kingdom",
            "segment": "distributor",
            "product": "paint roller covers",
            "material": "microfiber",
            "size": "9 inch",
            "quantity": "10,000 pieces",
            "oem_private_label": "private-label packaging",
            "destination": "United Kingdom",
        }

        result = qualify_inquiry(inquiry)

        self.assertEqual(result["qualification"]["grade"], "A")
        self.assertGreaterEqual(result["qualification"]["score"], 70)
        self.assertEqual(
            result["qualification"]["status"], "qualified_priority"
        )
        self.assertIn("15 minutes", result["qualification"]["next_action"])
        self.assertFalse(result["reply_draft"]["sent"])

    def test_unverified_company_cannot_be_grade_a(self) -> None:
        inquiry = {
            "company": "Unverified Buyer",
            "website": "https://buyer.example",
            "company_verified": False,
            "contact_name": "Taylor",
            "email": "taylor@buyer.example",
            "country": "United States",
            "segment": "importer",
            "product": "paint roller sets",
            "material": "polyester",
            "size": "9 inch",
            "quantity": "20,000 sets",
            "oem_private_label": "OEM logo and packaging",
        }

        result = qualify_inquiry(inquiry)

        self.assertEqual(result["qualification"]["grade"], "B")
        self.assertEqual(result["qualification"]["score"], 69)
        self.assertTrue(
            any(
                "capped" in evidence
                for evidence in result["qualification"]["score_evidence"]
            )
        )

    def test_sparse_inquiry_is_grade_c_and_requests_clarification(self) -> None:
        result = qualify_inquiry({"contact_name": "Morgan", "product": "brush"})

        self.assertEqual(result["qualification"]["grade"], "C")
        self.assertLessEqual(len(result["clarification_questions"]), 5)
        self.assertTrue(result["qualification"]["missing_identity_fields"])
        self.assertFalse(result["approval_gate"]["external_message_allowed"])
        self.assertFalse(result["approval_gate"]["crm_write_allowed"])

    def test_missing_quote_values_are_marked_for_verification(self) -> None:
        result = qualify_inquiry({"product": "paint roller"})

        self.assertEqual(
            result["quotation_checklist"]["quantity"], "Needs verification"
        )
        self.assertEqual(result["reply_draft"]["status"], "approval_required")

    def test_rejects_non_dictionary_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "dictionary"):
            qualify_inquiry([])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
