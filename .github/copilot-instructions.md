# Copilot Instructions for MarqueeMischief

Flask app (Python 3.13) with Jinja templates, SQLAlchemy/Flask-Migrate (Alembic), and a profanity filter.

## Environment
- Developed on **Windows**; code must also run on Linux. Write cross-platform code.
- Use `pathlib` / `os.path.join` for paths. Never hard-code `\` or `/` separators.
- Use PowerShell-compatible commands when suggesting terminal steps (no `&&`).
- Node.js is **not installed**. Do not use `node`, `npm`, or `npx`, and do not suggest JavaScript tooling. Use Python for scripts and checks.

## Portability rules
- Date formatting: use only portable `strftime` codes (`%Y %m %d %H %M %S %B %b %A %a`).
  Never use `%-d`, `%-m`, `%e`, `%k`, `%l`, `%P`, or `%#d`. For non-padded values use `.day`, `.month`, `.year` in Python or Jinja.
- Jinja evaluates `{{ }}` inside HTML comments. Disable template code with `{# ... #}`, not `<!-- -->`.
- Open text files with an explicit `encoding="utf-8"`.
- Avoid Unix-only modules/calls (`fcntl`, `os.fork`, `signal.SIGKILL`, etc.).

## Database
- Schema changes go through Flask-Migrate/Alembic: autogenerate a reviewed revision in `migrations/versions/`, then upgrade. Never alter the schema on app startup.

## Marquee rendering
- Marquees use the `3606-marquee-web` font at weight 900, with `@font-face` declared in each rendered marquee block (see `original_message_display.py`).

## Working practices
- Do not use APIs, flags, or library features you are not sure exist in the installed versions; check the installed package or docs first.
- After changing code or templates, run or render the affected code path to confirm it works before finishing.
- Keep changes small and focused; do not refactor unrelated code.
- Do not commit secrets or API keys.
