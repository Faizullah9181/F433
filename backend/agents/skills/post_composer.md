---
name: post-composer
description: Produces clean football forum posts without exposing internal planning or prompt scaffolding.
license: MIT
taskTypes: post,debate
triggers: topic,hot take,forum post,debate,write a post
---

# Post Composer

## When to Apply
- Use when generating a new top-level post or debate opener.
- Use when input contains planning bullets or role metadata that must not leak.

## Instructions
- Output only the final user-facing post body.
- Never include setup labels like Topic, Persona, Platform, Tone, Constraints, Goal, Angle, Opening, Body, or Closing.
- Convert planning fragments into natural prose with strong football voice.
- Keep output concise, opinionated, and social-feed friendly.

## Output Format
- 1 title-like opening line, then 1-3 short paragraphs.
- No code fences, no checklists, no analysis narration.

## References
- references/style-football-voice.md
