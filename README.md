# gh-action_jira-create

![GitHub Release](https://img.shields.io/github/v/release/SonarSource/gh-action_jira-create)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SonarSource_gh-action_jira-create&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SonarSource_gh-action_jira-create)
[![.github/workflows/it-test.yml](https://github.com/SonarSource/gh-action_jira-create/actions/workflows/it-test.yml/badge.svg)](https://github.com/SonarSource/gh-action_jira-create/actions/workflows/it-test.yml)

Create jira ticket

> Note
> This is a wrapper for GitHub action [atlassian/gajira-create](https://github.com/atlassian/gajira-create?tab=readme-ov-file)
> with some extra features such as Markdown support for issue description.

## Usage

### Create a simple Jira issue using Markdown

```yaml
steps:
  - uses: SonarSource/gh-action_jira-create@0.0.1 <--- replace with the last tag
    with:
      project: <Jira project key>
      issuetype: <Task, ...>
      summary: "Summary"
      description: "**some** description"
```

### Create a Jira issue with extra fields

```yaml
steps:
  - uses: SonarSource/gh-action_jira-create@0.0.1 <--- replace with the last tag
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

The `master` branch shall not be referenced by end-users,
please use tags instead and [Renovate](https://docs.renovatebot.com/) or
[Dependabot](https://docs.github.com/en/code-security/dependabot) to stay up to date.

## Contribute

Contributions are welcome, please have a look at [DEV.md](./DEV.md)
