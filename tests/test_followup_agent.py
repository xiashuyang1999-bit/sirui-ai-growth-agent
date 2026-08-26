"""Tests for approval-gated follow-up planning."""

import unittest

from agents.followup_agent import build_followup_plan


class FollowupAgentTests(unittest.TestCase):
    def test_grade_a_builds_five_unsent_followups(self) -> None:
        lead = {
            "record_id": "LEAD-001",
            "grade": "A",
            "stage": "qualified",
            "start_date": "2026-08-26",
            "company": "Example Distribution Ltd",
            "contact_name": "Alex",
            "market": "United Kingdom",
            "product": "paint roller covers",
        }

        plan = build_followup_plan(lead)

        self.assertEqual(plan["followup_agent_version"], "0.1")
        self.assertEqual(plan["sequence_status"], "active_draft")
        self.assertEqual(plan["summary"]["messages_drafted"], 5)
        self.assertEqual(
            [message["due_date"] for message in plan["followups"]],
            [
                "2026-08-29",
                "2026-09-02",
                "2026-09-09",
                "2026-09-16",
                "2026-09-25",
            ],
        )
        self.assertTrue(
            all(
                not message["sent"] and message["word_count"] < 120
                for message in plan["followups"]
            )
        )

    def test_stage_changes_the_first_followup_question(self) -> None:
        plan = build_followup_plan(
            {
                "grade": "B",
                "stage": "clarification",
                "start_date": "2026-08-26",
                "product": "paint roller sets",
            }
        )

        self.assertIn(
            "product specification, quantity, packaging, and destination",
            plan["followups"][0]["body"],
        )

    def test_observation_is_used_only_when_explicitly_verified(self) -> None:
        unverified = build_followup_plan(
            {
                "grade": "A",
                "start_date": "2026-08-26",
                "fit_observation": "the company sells paint rollers",
                "fit_observation_verified": False,
            }
        )
        verified = build_followup_plan(
            {
                "grade": "A",
                "start_date": "2026-08-26",
                "fit_observation": "the company sells paint rollers",
                "fit_observation_verified": True,
            }
        )

        self.assertNotIn(
            "the company sells paint rollers", unverified["followups"][0]["body"]
        )
        self.assertIn(
            "the company sells paint rollers", verified["followups"][0]["body"]
        )

    def test_grade_c_does_not_create_proactive_sequence(self) -> None:
        plan = build_followup_plan(
            {"grade": "C", "start_date": "2026-08-26"}
        )

        self.assertEqual(plan["sequence_status"], "not_recommended")
        self.assertEqual(plan["followups"], [])
        self.assertEqual(plan["summary"]["messages_sent"], 0)
        self.assertFalse(plan["approval_gate"]["external_message_allowed"])

    def test_rejects_invalid_start_date(self) -> None:
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            build_followup_plan({"grade": "A", "start_date": "26/08/2026"})


if __name__ == "__main__":
    unittest.main()
