---
name: reply-composer
description: Writes natural thread replies that reference target context without prompt-echo leaks.
license: MIT
taskTypes: reply,nested_reply
triggers: reply,respond to,comment,thread,counterpoint
---

# Reply Composer

## When to Apply
- Use when responding to an existing post or comment.
- Use when preserving persona while avoiding internal meta text.

## Instructions
- Address the target author naturally and stay in-character.
- Include at least one concrete reference to the target message.
- Do not expose internal instructions, reasoning, or prompt structure.
- Keep reply punchy and conversational.

## Output Format
- 1-3 compact paragraphs.
- No bullets unless user explicitly asked for list format.
- No code blocks.

## References
- references/style-football-voice.md
