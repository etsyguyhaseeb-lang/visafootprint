# Tools

Python scripts for deterministic execution. Each script does one thing reliably.

## Conventions

- Scripts accept arguments via CLI flags or read from `.env`
- All output goes to stdout (JSON preferred) or writes to `.tmp/`
- Credentials come from `.env` only — never hardcoded
- Each script exits with code `0` on success, non-zero on failure

## Adding a New Tool

1. Create `tools/your_tool_name.py`
2. Add a docstring at the top describing what it does, inputs, and outputs
3. Use `python-dotenv` to load `.env`
4. Test it standalone before wiring into a workflow
