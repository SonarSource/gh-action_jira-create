# gh-action_jira-create

![GitHub Release](https://img.shields.io/github/v/release/SonarSource/gh-action_jira-create)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SonarSource_gh-action_jira-create&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SonarSource_gh-action_jira-create)
[![.github/workflows/it-test.yml](https://github.com/SonarSource/gh-action_jira-create/actions/workflows/it-test.yml/badge.svg)](https://github.com/SonarSource/gh-action_jira-create/actions/workflows/it-test.yml)

Create Jira ticket

Create issues through Jira Cloud REST API v2. Markdown descriptions are converted to Jira markup.

## Requirements and authentication

The runner must provide Bash, Python 3 and curl. No Python packages are required.
Provide `JIRA_BASE_URL`, `JIRA_USER_EMAIL` and `JIRA_API_TOKEN` through the step environment.
The base URL must use HTTPS and must not contain credentials, a query or a fragment.
Custom Jira hosts and context paths are supported.

For workflows that already use Jira Login, the action also reads `$HOME/jira/config.yml`.
It accepts the `baseUrl`, `email` and `token` scalar values written by Jira Login,
including plain, single-quoted and JSON-compatible double-quoted strings.
Each environment value takes precedence independently. Missing values fall back to the file.
YAML tags, aliases, collections and multiline credential values are not supported.
Do not print the configuration or commit credentials.

The action does not follow HTTP redirects or automatically retry issue creation.
If a request fails after Jira receives it, check Jira before retrying to avoid duplicate issues.

## Usage

### Create a simple Jira issue using Markdown

```yaml
steps:
  - uses: SonarSource/gh-action_jira-create@0.0.1 # Replace with the latest tag
    env:
      JIRA_BASE_URL: ${{ vars.JIRA_BASE_URL }}
      JIRA_USER_EMAIL: ${{ secrets.JIRA_USER_EMAIL }}
      JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
    with:
      project: <Jira project key>
      issuetype: <Task, ...>
      summary: "Summary"
      description: "**some** description"
```

### Create a Jira issue with extra fields

```yaml
steps:
  - uses: SonarSource/gh-action_jira-create@0.0.1 # Replace with the latest tag
    env:
      JIRA_BASE_URL: ${{ vars.JIRA_BASE_URL }}
      JIRA_USER_EMAIL: ${{ secrets.JIRA_USER_EMAIL }}
      JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
    with:
      project: <Jira project key>
      issuetype: <Task, ...>
      summary: "Summary"
      description: "**some** description"
      fields: |
        {
          "priority": {"name": "Normal"}
        }
```

## Inputs

| Input name    | Description                                           | Required |
|---------------|-------------------------------------------------------|----------|
| `project`     | Specify Jira project key                              | yes      |
| `issuetype`   | Jira issue type (i.e: Task)                           | yes      |
| `summary`     | Summary (= title) of the Jira issue                   | yes      |
| `description` | Description of the Jira issue (Markdown is supported) | no       |
| `fields`      | Allow to define some extra fields such as `priority`  | no       |

The `fields` input must be a JSON object. It must not contain `project`, `issuetype`,
`summary` or `description`. Use the named inputs for these values. Conflicts fail before
the action sends a request.

## Outputs

| Input name    | Description                                           |
|---------------|-------------------------------------------------------|
| `issue`       | Issue identifier (i.e: `JIRA-42`)                     |

## Versioning

This project is using [Semantic Versioning](https://semver.org/).

The `master` branch shall not be referenced by end-users.
Please use tags instead and [Renovate](https://docs.renovatebot.com/) or
[Dependabot](https://docs.github.com/en/code-security/dependabot) to stay up to date.

## Contribute

Contributions are welcome, please have a look at [DEV.md](./DEV.md)
