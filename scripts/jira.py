"""Jira REST transport shared by the composite action and sandbox tests."""

import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


class JiraError(Exception):
    """An error safe to report without request or response data."""


def login_config(path):
    """Read scalar values emitted by Jira Login without evaluating YAML tags."""
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(baseUrl|email|token):(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        value = value.strip()
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError as error:
                raise JiraError("Invalid quoted Jira Login value") from error
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        elif value.startswith(("!", "&", "*", "|", ">", "[", "{")):
            raise JiraError("Jira Login values must be scalar strings")
        else:
            value = value.split(" #", maxsplit=1)[0].split("\t#", maxsplit=1)[0].rstrip()
        if not isinstance(value, str):
            raise JiraError("Jira Login values must be strings")
        values[key] = value
    return values


def credentials():
    names = {"JIRA_BASE_URL": "baseUrl", "JIRA_USER_EMAIL": "email", "JIRA_API_TOKEN": "token"}
    config = {}
    path = Path.home() / "jira/config.yml"
    if any(not os.environ.get(name) for name in names) and path.is_file():
        config = login_config(path)
    result = [os.environ.get(name) or config.get(key, "") for name, key in names.items()]
    for name, value in zip(names, result):
        if not value:
            raise JiraError(f"{name} must be set in the environment or Jira Login configuration")
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise JiraError(f"{name} must not contain control characters")
    url = urlsplit(result[0])
    try:
        port = url.port
    except ValueError as error:
        raise JiraError("Invalid Jira base URL port") from error
    if (url.scheme != "https" or not url.hostname or url.username is not None
            or url.password is not None or url.query or url.fragment
            or "?" in result[0] or "#" in result[0]
            or "\\" in result[0] or any(c.isspace() for c in result[0])
            or (port is not None and port < 1)):
        raise JiraError("JIRA_BASE_URL must be an HTTPS URL without credentials, query or fragment")
    result[0] = result[0].rstrip("/")
    return result


def curl_quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


class Jira:
    def __init__(self):
        self.url, email, token = credentials()
        self.authorization = base64.b64encode(f"{email}:{token}".encode()).decode()

    def request(self, method, resource, payload=None):
        # Keep credentials and response bodies out of arguments and diagnostics.
        with tempfile.TemporaryDirectory(prefix="jira-rest-") as directory:
            root = Path(directory)
            config = root / "curl.conf"
            response = root / "response.json"
            options = [
                'header = ' + curl_quote("Authorization: Basic " + self.authorization),
                'header = "Accept: application/json"',
                'header = "Content-Type: application/json"',
                'url = ' + curl_quote(self.url + "/rest/api/2/" + resource),
            ]
            config.write_text("\n".join(options) + "\n", encoding="utf-8")
            config.chmod(0o600)
            command = ["curl", "--disable", "--config", str(config), "--silent",
                       "--proto", "=https", "--connect-timeout", "15", "--max-time", "60",
                       "--request", method, "--output", str(response), "--write-out", "%{http_code}"]
            if payload is not None:
                command.extend(["--data-binary", "@-"])
            completed = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                                       text=True, capture_output=True, check=False)
            if completed.returncode:
                raise JiraError("Jira transport failed; outcome may be uncertain. Do not blindly retry creation.")
            expected = "200"
            if method == "POST":
                expected = "201" if resource == "issue" else "204"
            if completed.stdout != expected:
                raise JiraError("Jira HTTP request failed (status "
                                + (completed.stdout if re.fullmatch(r"\d{3}", completed.stdout) else "unknown") + ")")
            if expected == "204":
                return None
            try:
                return json.loads(response.read_text(encoding="utf-8"))
            except (ValueError, OSError) as error:
                raise JiraError("Invalid Jira response; do not blindly retry creation") from error


def create_payload():
    fields_text = os.environ.get("INPUT_FIELDS", "")
    try:
        extra = json.loads(fields_text) if fields_text.strip() else {}
    except ValueError as error:
        raise JiraError("fields must be a JSON object") from error
    if not isinstance(extra, dict):
        raise JiraError("fields must be a JSON object")
    reserved = {"project", "issuetype", "summary", "description"}
    if reserved.intersection(extra):
        raise JiraError("fields must not override project, issuetype, summary or description")
    for name in ("PROJECT", "ISSUETYPE", "SUMMARY"):
        if not os.environ.get("INPUT_" + name, "").strip():
            raise JiraError(name.lower() + " is required")
    fields = {**extra,
              "project": {"key": os.environ["INPUT_PROJECT"]},
              "issuetype": {"name": os.environ["INPUT_ISSUETYPE"]},
              "summary": os.environ["INPUT_SUMMARY"]}
    if os.environ.get("INPUT_DESCRIPTION"):
        fields["description"] = os.environ["INPUT_DESCRIPTION"]
    return {"fields": fields}


def issue_key(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z\d_]*-[1-9]\d*", value):
        raise JiraError("Jira response did not contain a valid issue key; do not blindly retry creation")
    return value


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"create", "get", "cleanup", "write-config"}:
        raise JiraError("Expected create, get, cleanup or write-config")
    operation = sys.argv[1]
    if operation == "write-config":
        url, email, token = credentials()
        path = Path.home() / "jira/config.yml"
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        # JSON strings are also YAML scalars, including quotes and backslashes.
        with path.open("x", encoding="utf-8") as stream:
            path.chmod(0o600)
            for name, value in (("baseUrl", url), ("email", email), ("token", token)):
                stream.write(name + ": " + json.dumps(value) + "\n")
        return
    if operation == "create":
        payload = create_payload()
        response = Jira().request("POST", "issue", payload)
        key = issue_key(response.get("key") if isinstance(response, dict) else None)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("issue=" + key + "\n")
        return
    key = issue_key(os.environ.get("ISSUE_KEY"))
    client = Jira()
    if operation == "get":
        response = client.request("GET", "issue/" + key)
        # One-line encoded JSON cannot inject additional GitHub output records.
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("json_payload=" + json.dumps(response, separators=(",", ":")) + "\n")
    else:
        cleanup(client, key)


def cleanup(client, key):
    import time

    resource = "issue/" + key
    for target in ("Resolved", "Closed"):
        for attempt in range(13):
            current = client.request("GET", resource)
            if current["fields"]["status"]["name"].casefold() in {target.casefold(), "closed"}:
                break
            if attempt == 12:
                raise JiraError("Test issue did not reach " + target + " within the polling limit")
            transitions = client.request("GET", resource + "/transitions")["transitions"]
            transition = next((t for t in transitions if t.get("to", {}).get("name", "").casefold()
                               == target.casefold()), None)
            if transition:
                client.request("POST", resource + "/transitions", {"transition": {"id": transition["id"]}})
            time.sleep(5)
        print("Test issue reached " + target)


if __name__ == "__main__":
    try:
        main()
    except (JiraError, OSError, ValueError, KeyError, TypeError) as error:
        # Unexpected exceptions also use a fixed message to avoid leaking remote data.
        print("::error::" + (str(error) if isinstance(error, JiraError) else "Jira operation failed"), file=sys.stderr)
        sys.exit(1)
