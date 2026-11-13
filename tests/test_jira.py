"""Offline contract tests. The fake curl never makes a network request."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("jira", ROOT / "scripts/jira.py")
jira = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(jira)


class JiraTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {"HOME": str(self.root), "PATH": os.environ["PATH"],
                    "JIRA_BASE_URL": "https://jira.example.test", "JIRA_USER_EMAIL": "test@example.test",
                    "JIRA_API_TOKEN": "offline-placeholder", "INPUT_PROJECT": "BUILD",
                    "INPUT_ISSUETYPE": "Feature", "INPUT_SUMMARY": 'A "quote"\n$literal',
                    "GITHUB_OUTPUT": str(self.root / "output")}
        self.patcher = patch.dict(os.environ, self.env, clear=True)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def config(self, text):
        path = self.root / "jira/config.yml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
        return path

    def test_optional_description_is_omitted_when_empty(self):
        for value in (None, ""):
            with self.subTest(description=value):
                if value is None:
                    os.environ.pop("INPUT_DESCRIPTION", None)
                else:
                    os.environ["INPUT_DESCRIPTION"] = value
                result = self.run_create()
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads((self.root / "payload").read_text())
                self.assertNotIn("description", payload["fields"])

    def test_payload_json_and_fields(self):
        os.environ["INPUT_FIELDS"] = '{"priority":{"name":"Normal"}}'
        os.environ["INPUT_DESCRIPTION"] = 'line one\n"line two"'
        result = json.loads(json.dumps(jira.create_payload()))["fields"]
        self.assertEqual(result["summary"], self.env["INPUT_SUMMARY"])
        self.assertEqual(result["description"], os.environ["INPUT_DESCRIPTION"])
        self.assertEqual(result["priority"], {"name": "Normal"})

    def test_invalid_and_conflicting_fields(self):
        for value in ("[", "[]", "null", '"text"', "42", '{"summary":"override"}',
                      '{"description":"override"}', '{"project":{}}', '{"issuetype":{}}'):
            with self.subTest(value=value), patch.dict(os.environ, INPUT_FIELDS=value):
                with self.assertRaises(jira.JiraError):
                    jira.create_payload()

    def test_required_inputs(self):
        for name in ("INPUT_PROJECT", "INPUT_ISSUETYPE", "INPUT_SUMMARY"):
            with patch.dict(os.environ, {name: ""}), self.assertRaises(jira.JiraError):
                jira.create_payload()

    def test_config_and_mixed_credentials(self):
        self.config('baseUrl: https://config.example.test\nemail: \'config@example.test\'\ntoken: "config-placeholder"\n')
        with patch.dict(os.environ, JIRA_BASE_URL="", JIRA_USER_EMAIL="", JIRA_API_TOKEN=""):
            self.assertEqual(jira.credentials(), ["https://config.example.test", "config@example.test", "config-placeholder"])
        with patch.dict(os.environ, JIRA_USER_EMAIL="", JIRA_API_TOKEN=""):
            self.assertEqual(jira.credentials()[0], self.env["JIRA_BASE_URL"])
            self.assertEqual(jira.credentials()[1:], ["config@example.test", "config-placeholder"])

    def test_missing_credentials(self):
        for name in ("JIRA_BASE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN"):
            with patch.dict(os.environ, {name: ""}), self.assertRaisesRegex(jira.JiraError, name):
                jira.credentials()

    def test_config_quotes_and_no_evaluation(self):
        path = self.config('email: \'it\'\'s@example.test\'\ntoken: "a\\\\b\\\"c"\n')
        self.assertEqual(jira.login_config(path), {"email": "it's@example.test", "token": 'a\\b"c'})
        for text in ('token: !unsafe value', 'token: "unterminated', 'token: [a, b]'):
            path = self.config(text)
            with self.subTest(text=text), self.assertRaises(jira.JiraError):
                jira.login_config(path)

    def test_rejected_urls(self):
        for url in ("http://jira.test", "https://u:p@jira.test", "https://jira.test?x=y",
                    "https://jira.test#x", "https://jira.test/\\evil", "https://jira.test/\nheader",
                    "https:///path", "https://jira.test:bad", "https://jira.test:0", "https://jira.test?"):
            with self.subTest(url=url), patch.dict(os.environ, JIRA_BASE_URL=url):
                with self.assertRaises((jira.JiraError, ValueError)):
                    jira.credentials()
        with patch.dict(os.environ, JIRA_BASE_URL="https://custom.example.test/jira/"):
            self.assertEqual(jira.credentials()[0], "https://custom.example.test/jira")

    def run_create(self, status="201", response='{"key":"BUILD-123"}', exit_code=0):
        fake = self.root / "curl"
        fake.write_text('''#!/usr/bin/python3
import json,os,pathlib,sys
args=sys.argv[1:]
assert args[0] == '--disable'
assert '--location' not in args and '--retry' not in args
assert not any('offline-placeholder' in a for a in args)
config=pathlib.Path(args[args.index('--config')+1])
assert config.stat().st_mode & 0o777 == 0o600
pathlib.Path(os.environ['FAKE_CONFIG_PATH']).write_text(str(config))
pathlib.Path(os.environ['FAKE_PAYLOAD']).write_text(sys.stdin.read())
pathlib.Path(args[args.index('--output')+1]).write_text(os.environ['FAKE_RESPONSE'])
print(os.environ['FAKE_STATUS'],end='')
print('untrusted response diagnostic',file=sys.stderr)
sys.exit(int(os.environ['FAKE_EXIT']))
''')
        fake.chmod(0o700)
        environment = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ["PATH"],
                           FAKE_CONFIG_PATH=str(self.root / "config-path"), FAKE_PAYLOAD=str(self.root / "payload"),
                           FAKE_STATUS=status, FAKE_RESPONSE=response, FAKE_EXIT=str(exit_code))
        result = subprocess.run(["python3", str(ROOT / "scripts/jira.py"), "create"],
                                env=environment, text=True, capture_output=True, check=False)
        self.assertNotIn("untrusted response diagnostic", result.stderr)
        self.assertNotIn("offline-placeholder", result.stderr)
        self.assertFalse(Path((self.root / "config-path").read_text()).exists())
        return result

    def test_create_transport_contract(self):
        result = self.run_create()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "output").read_text(), "issue=BUILD-123\n")
        self.assertEqual(json.loads((self.root / "payload").read_text())["fields"]["summary"], self.env["INPUT_SUMMARY"])

    def test_http_failure_and_uncertain_creation(self):
        for status, response, code in (("401", "untrusted body", 0), ("302", "redirect", 0),
                                       ("201", "not json", 0), ("201", "{}", 0),
                                       ("201", '{"key":"BUILD-1\\nmalicious=1"}', 0), ("000", "", 28)):
            with self.subTest(status=status, response=response, code=code):
                result = self.run_create(status, response, code)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / "output").exists())

    def test_cleanup_checks_status_after_transition(self):
        from unittest.mock import Mock
        client = Mock()
        client.request.side_effect = [
            {"fields": {"status": {"name": "Open"}}},
            {"transitions": [{"id": "5", "to": {"name": "Resolved"}}]}, None,
            {"fields": {"status": {"name": "Resolved"}}},
            {"fields": {"status": {"name": "Resolved"}}},
            {"transitions": [{"id": "6", "to": {"name": "Closed"}}]}, None,
            {"fields": {"status": {"name": "Closed"}}},
        ]
        with patch("time.sleep"):
            jira.cleanup(client, "BUILD-123")
        self.assertEqual(client.request.call_count, 8)

    def test_cleanup_confirms_last_allowed_transition(self):
        from unittest.mock import Mock
        client = Mock()
        open_issue = {"fields": {"status": {"name": "Open"}}}
        resolved = {"fields": {"status": {"name": "Resolved"}}}
        client.request.side_effect = [open_issue, {"transitions": []}] * 11 + [
            open_issue, {"transitions": [{"id": "5", "to": {"name": "Resolved"}}]}, None,
            resolved, resolved, {"transitions": [{"id": "6", "to": {"name": "Closed"}}]}, None,
            {"fields": {"status": {"name": "Closed"}}},
        ]
        with patch("time.sleep"):
            jira.cleanup(client, "BUILD-123")
        self.assertEqual(client.request.call_count, 30)


if __name__ == "__main__":
    unittest.main()
