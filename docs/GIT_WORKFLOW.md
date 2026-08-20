# Git Workflow

## Core Principles
The canonical repository is: `s4meer-dev/knowUrDB`

- `main` branch is the stable branch.
- feature branches may be used for larger features.
- **no force push**.
- **no secrets committed**.
- inspect `git status` before commit.
- inspect `git diff` before commit.
- meaningful commit messages.
- every completed phase gets its own commit.
- every completed phase is pushed to GitHub.
- verify remote state after pushing.

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
