# Developer notes

> You want to contribute to this project ? Please read the following

## IT Tests

This project defines integration tests in `.github/workflows/it-test.yml`.

Test assertions are done using [nick-fields/assert-action](https://github.com/nick-fields/assert-action).

Resources used for tests are placed within `.github/tests/resources/` directory

### Side note

At the moment, GitHub branch protection does not allow to define checks based
on a REGEX as we can find in other CI tools such as Jenkins.

In order to work around this limitation, this project make
use of [step-security/alls-green](https://github.com/step-security/alls-green) (a StepSecurity-maintained fork of re-actors/alls-green).

All tests have to be declared in `.github/workflows/it-test.yml`.
The job called `it-tests` declares a list of needs:

```yaml
    ...
    needs:
       ...
      - offline-tests
      - it-tests-use-only-required-input-values
      - it-tests-check-all-inputs
      - it-tests-description-markdown-to-jira-markup-conversion
      - < your new test > <-------------- Add your tests here
```

## Local checks

Run `python3 -m unittest discover -s tests -v` for the offline REST contract tests.
The fake curl executable checks request payloads, credential isolation and temporary-file cleanup.
Run `pre-commit run --all-files` for formatting and workflow validation.
The three sandbox integration jobs require Vault access in GitHub Actions.
Each job retrieves the created issue and attempts resolution and closure even if an assertion fails.
Cleanup polls for each target status and fails if Jira does not confirm the transition.
