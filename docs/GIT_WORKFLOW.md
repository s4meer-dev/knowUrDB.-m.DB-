# Git Workflow

## Core Principles
The canonical repository is: `s4meer-dev/knowUrDB`
The canonical GitHub account is: `s4meer-dev`

- `main` branch is the stable branch. All commits go here unless using feature branches for larger features.
- **Repository-local Git identity**: Must be configured with `user.name` and `user.email`. Git author email must be a verified email associated with the `s4meer-dev` GitHub account.
- **Pre-commit verification**: Verify current branch is `main`, remote is `s4meer-dev/knowUrDB`, and author identity is correctly set before committing.
- **Testing before commit**: Run tests, lint, and build (where applicable) before committing.
- **Diff review**: Always inspect `git status` and `git diff` before commit.
- **Commit attribution requirements**: Every commit must be attributed to the correct GitHub account.
- **No force pushes**: Never force push to `main` unless explicitly authorized.
- **No rewriting published history**: Do not rebase, amend, or rewrite history on the `main` branch.
- **Push verification**: Verify remote state after pushing to ensure local `main` matches `origin/main`.
- **No secrets committed**: Ensure all credentials and secrets are protected via `.gitignore`.
- **Meaningful commits**: Use Conventional Commits formatting and ensure every commit represents a meaningful change.

## Merge Strategy
- Pull/merge strategy with review before merge.
- Phase-based commits.

## Commit Naming Convention
Recommended commit style:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for code restructuring
- `test:` for adding or updating tests
- `docs:` for documentation changes
- `chore:` for maintenance tasks
- `security:` for security-related updates

### Recommended Phase commit format:
`chore: establish knowUrDB architecture and engineering foundation`

### Future examples:
- `feat: add demo database`
- `feat: implement database upload`
- `feat: implement schema analyzer`
- `feat: integrate Gemini provider`
- `feat: implement text to SQL generation`
- `feat: add SQL validation`
- `test: add text to SQL evaluation benchmark`
