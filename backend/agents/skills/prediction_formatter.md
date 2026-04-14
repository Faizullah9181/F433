---
name: prediction-formatter
description: Formats match predictions with clear scoreline, rationale, and confidence while keeping output user-facing.
license: MIT
taskTypes: prediction
triggers: prediction,predict,scoreline,fixture,confidence
---

# Prediction Formatter

## When to Apply
- Use when producing match predictions from tool/data context.
- Use when model may output planning or step-by-step scratch text.

## Instructions
- Include a clear predicted scoreline.
- Give concise rationale tied to football signals (form, matchup, injuries, trends).
- Keep tone assertive but readable.
- Never expose tool instructions or hidden reasoning steps.

## Output Format
- Scoreline line.
- 2-4 sentences rationale.
- Optional confidence tag at end.

## References
- references/style-football-voice.md
