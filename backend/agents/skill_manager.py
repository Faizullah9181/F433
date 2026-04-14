"""Skill registry for progressive prompt disclosure (L1/L2/L3-style)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"
RUNTIME_DIR = SKILLS_DIR / "runtime"


@dataclass
class SkillSpec:
    name: str
    description: str
    task_types: list[str]
    triggers: list[str]
    instructions: str
    references: list[str]
    source_path: Path


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse simple YAML-like frontmatter and return metadata + remaining body."""
    if not text.startswith("---\n"):
        return {}, text

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    block = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, body


def _split_csv(raw: str) -> list[str]:
    if not raw:
        return []
    cleaned = raw.strip().strip("[]")
    return [p.strip().strip('"').strip("'").lower() for p in cleaned.split(",") if p.strip()]


def _split_section(body: str, section: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(section)}\s*$", flags=re.IGNORECASE | re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""
    start = match.end()
    next_header = re.search(r"^##\s+", body[start:], flags=re.MULTILINE)
    end = start + next_header.start() if next_header else len(body)
    return body[start:end].strip()


def _parse_skill_file(path: Path) -> SkillSpec | None:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None

    meta, body = _parse_frontmatter(text)

    # Preferred: frontmatter-based format.
    if meta.get("name"):
        name = meta["name"]
        description = meta.get("description", "No description")
        task_types = _split_csv(meta.get("tasktypes", "") or meta.get("task_types", ""))
        triggers = _split_csv(meta.get("triggers", ""))

        instructions = _split_section(body, "Instructions")
        if not instructions:
            instructions = _split_section(body, "Process")
        if not instructions:
            instructions = _split_section(body, "Research Process")

        refs_raw = _split_section(body, "References")
        references = [ln.strip("- ").strip() for ln in refs_raw.splitlines() if ln.strip()]

        return SkillSpec(
            name=name,
            description=description,
            task_types=task_types,
            triggers=triggers,
            instructions=instructions,
            references=references,
            source_path=path,
        )

    # Legacy fallback format.
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# Skill:"):
        return None

    name = lines[0].split(":", 1)[1].strip()
    description = ""
    task_types: list[str] = []
    triggers: list[str] = []

    for line in lines[1:12]:
        if line.startswith("Description:"):
            description = line.split(":", 1)[1].strip()
        elif line.startswith("TaskTypes:"):
            raw = line.split(":", 1)[1].strip()
            task_types = [p.strip().lower() for p in raw.split(",") if p.strip()]
        elif line.startswith("Triggers:"):
            raw = line.split(":", 1)[1].strip()
            triggers = [p.strip().lower() for p in raw.split(",") if p.strip()]

    instructions = _split_section(text, "Instructions")
    refs_raw = _split_section(text, "References")
    references = [ln.strip("- ").strip() for ln in refs_raw.splitlines() if ln.strip()]

    return SkillSpec(
        name=name,
        description=description or "No description",
        task_types=task_types,
        triggers=triggers,
        instructions=instructions,
        references=references,
        source_path=path,
    )


def load_skills() -> list[SkillSpec]:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    skills: list[SkillSpec] = []
    for path in sorted(SKILLS_DIR.glob("*.md")) + sorted(RUNTIME_DIR.glob("*.md")):
        spec = _parse_skill_file(path)
        if spec:
            skills.append(spec)
    return skills


def skill_catalog_text(max_tokens_per_skill: int = 100) -> str:
    """L1 metadata: short menu always loaded into baseline prompt."""
    skills = load_skills()
    if not skills:
        return "(no skills loaded)"

    rows = []
    for s in skills:
        task_part = "/".join(s.task_types[:3]) if s.task_types else "general"
        trigger_part = ", ".join(s.triggers[:4]) if s.triggers else "none"
        line = f"- {s.name}: {s.description} | tasks={task_part} | triggers={trigger_part}"
        rows.append(" ".join(line.split())[: max_tokens_per_skill * 5])
    return "\n".join(rows)


def _score_skill(spec: SkillSpec, task_type: str, prompt: str) -> int:
    score = 0
    p = prompt.lower()

    if task_type.lower() in spec.task_types:
        score += 4

    for trig in spec.triggers:
        if trig and trig in p:
            score += 2

    return score


def active_skill_instructions(task_type: str, prompt: str, max_skills: int = 2) -> list[SkillSpec]:
    """L2/L3 load: choose and return only relevant full skills."""
    skills = load_skills()
    ranked = sorted(
        ((spec, _score_skill(spec, task_type, prompt)) for spec in skills), key=lambda x: x[1], reverse=True
    )
    selected = [spec for spec, score in ranked if score > 0][:max_skills]
    return selected


def build_skill_context(task_type: str, prompt: str) -> str:
    selected = active_skill_instructions(task_type, prompt)
    if not selected:
        return ""

    blocks: list[str] = []
    for skill in selected:
        ref_blocks: list[str] = []
        for ref in skill.references[:2]:
            ref_path = (skill.source_path.parent / ref).resolve()
            if ref_path.exists() and ref_path.is_file():
                ref_text = ref_path.read_text(encoding="utf-8").strip()
                ref_blocks.append(f"{ref}:\n{ref_text[:1200]}")
            else:
                ref_blocks.append(f"{ref}: (not found)")
        refs = "\n\n".join(ref_blocks) if ref_blocks else "none"
        blocks.append(
            f"Skill: {skill.name}\n"
            f"Description: {skill.description}\n"
            f"Instructions:\n{skill.instructions or '- none'}\n"
            f"References:\n{refs}"
        )

    return "\n\n".join(blocks)


def list_skill_metadata() -> list[dict]:
    return [
        {
            "name": s.name,
            "description": s.description,
            "task_types": s.task_types,
            "triggers": s.triggers,
            "references": s.references,
        }
        for s in load_skills()
    ]


def create_runtime_skill(
    *,
    name: str,
    description: str,
    task_types: list[str],
    triggers: list[str],
    instructions: str,
    references: list[str] | None = None,
) -> Path:
    """Meta-skill support: persist a new skill at runtime."""
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower())
    if not safe_name:
        raise ValueError("Skill name cannot be empty")

    references = references or []
    content = (
        "---\n"
        f"name: {safe_name}\n"
        f"description: {description.strip()}\n"
        "license: MIT\n"
        f"taskTypes: {', '.join(task_types)}\n"
        f"triggers: {', '.join(triggers)}\n"
        "---\n\n"
        f"# {safe_name.replace('-', ' ').replace('_', ' ').title()}\n\n"
        "## When to Apply\n"
        "- Apply when user request matches the trigger conditions.\n"
        "- Use the skill to produce user-facing output only.\n\n"
        "## Instructions\n"
        f"{instructions.strip()}\n\n"
        "## References\n" + ("\n".join(f"- {r}" for r in references) if references else "- none") + "\n"
    )

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNTIME_DIR / f"{safe_name}.md"
    path.write_text(content, encoding="utf-8")
    return path
