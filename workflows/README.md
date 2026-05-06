# Workflows

Markdown SOPs that define what to do and how. These are the instructions I follow.

## Structure of a Workflow File

```
# Workflow Name

## Objective
What this workflow accomplishes.

## Inputs Required
- input_1: description
- input_2: description

## Steps
1. Step description → tool: `tools/script_name.py`
2. Next step...

## Expected Output
What success looks like.

## Edge Cases & Notes
- Known rate limits, quirks, or failure modes
- Updated as the system learns
```

## Naming Convention

`verb_noun.md` — e.g., `scan_twitter.md`, `export_to_sheets.md`, `summarize_mentions.md`
