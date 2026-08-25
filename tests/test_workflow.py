"""Tests for the command-line workflow without making network requests."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow.main import run_audit


class AuditWorkflowTests(unittest.TestCase):
    @patch("workflow.main.audit_site")
    def test_run_audit_saves_json_report(self, audit_site) -> None:
        audit_site.return_value = {
            "agent_version": "0.3",
            "summary": {
                "status": "pass",
                "pages_audited": 1,
                "pages_failed": 0,
            },
            "pages": [],
            "errors": [],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "audit.json"
            result_path = run_audit(
                "https://example.com", max_pages=1, output=output
            )
            saved_report = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(saved_report["agent_version"], "0.3")
        self.assertEqual(saved_report["summary"]["status"], "pass")
        audit_site.assert_called_once_with("https://example.com", max_pages=1)


if __name__ == "__main__":
    unittest.main()
