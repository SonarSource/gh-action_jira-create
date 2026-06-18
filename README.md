# gh-action_jira-create

![GitHub Release](https://img.shields.io/github/v/release/SonarSource/gh-action_jira-create)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SonarSource_gh-action_jira-create&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SonarSource_gh-action_jira-create)
[![.github/workflows/it-test.yml](https://github.com/SonarSource/gh-action_jira-create/actions/workflows/it-test.yml/badge.svg)](https://github.com/SonarSource/gh-action_jira-create/actions/workflows/it-test.yml)

Create Jira ticket

> Note
> This action creates the issue by calling the Jira Cloud REST API (v2) directly. It keeps
> Markdown support for the issue description (converted to Jira wiki markup).
>
> It previously wrapped [atlassian/gajira-create](https://github.com/atlassian/gajira-create),
> which was dropped because it is stuck on Node 16/20 and unmaintained (see BUILD-11506).

## Requirements

The action runs a small Bash script, so the runner must have **`bash`**, **`curl`**, and **`jq`**
available in `PATH` (GitHub-hosted Ubuntu runners include them by default).

## Authentication

The action authenticates against Jira using **three environment variables** that you must set
on the step (or job). They are the same variables the old `atlassian/gajira-login` consumed:

| Env var | Description |
|-----------------|-------------------------------------------------|
| `JIRA_BASE_URL` | Base URL of the Jira instance (e.g. `https://xxx.atlassian.net`) |
| `JIRA_USER_EMAIL` | Email of the Jira user / token owner |
| `JIRA_API_TOKEN` | Jira API token (password) for that user |

> Migration note: callers no longer run a separate `atlassian/gajira-login` step — instead pass
> the three variables above as `env:` on the `gh-action_jira-create` step.

## Usage

### Create a simple Jira issue using Markdown

```yaml
steps:
  - uses: SonarSource/gh-action_jira-create@0.0.1 # <--- replace with the last tag
    env:
      JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
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
  - uses: SonarSource/gh-action_jira-create@0.0.1 # <--- replace with the last tag
    env:
      JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
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
