# Contributing

Thanks for contributing to DocketBird MCP. Bug reports, documentation fixes, and
focused pull requests are welcome.

## Before you start

- Search the existing issues before opening a new one.
- For substantial changes, open an issue first so the approach and scope can be
  discussed.
- Never include real DocketBird API keys, OAuth tokens, service tokens, user data,
  or court documents in issues, commits, logs, or test fixtures.
- Report suspected vulnerabilities privately as described in
  [SECURITY.md](SECURITY.md), not in a public issue.

## Local setup

The project requires Python 3.11 and uses `uv` for local development:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Run the offline checks before submitting a pull request:

```bash
pytest
ruff check .
```

The test suite fakes network access. New tests must also run without DocketBird
credentials or calls to live services.

## Pull requests

- Branch from `main` and keep each pull request focused on one change.
- Add or update tests when behavior changes.
- Keep `README.md`, `docs/`, and `skills/docketbird-mcp/` in sync with tool or
  interface changes.
- Explain the change, its motivation, and the validation performed.
- Do not modify deployment secrets or include production data.

By contributing, you agree that your contribution is licensed under the
[Apache License 2.0](LICENSE).
