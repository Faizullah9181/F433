---
name: skill-creator
description: Generates new SKILL.md definitions in spec-style format for runtime capability extension.
license: MIT
taskTypes: skill_factory
triggers: create skill,new skill,skill factory,capability gap,runtime skill
---

# Skill Creator

## When to Apply
- Use when a request requires a capability not covered by existing skills.
- Use when asked to generate a reusable skill definition.

## Instructions
- Return exactly one JSON object with keys:
  name, description, task_types, triggers, instructions, references.
- Keep name machine-friendly (lowercase, dashes/underscores).
- Make instructions concrete, actionable, and user-safe.
- Keep references optional and relevant.
- Do not return markdown fences around JSON.

## Output Format
- Strict JSON object only.

## References
- references/agent-skills-spec.md
