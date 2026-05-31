from __future__ import annotations

import logging
import re
from typing import Any

from . import llm, tools

logger = logging.getLogger("agent.meeting_notes")

_EXTRACT_SYSTEM_PROMPT = (
    "Kamu asisten yang mengekstrak action items dari catatan meeting. "
    "Dari transkrip meeting yang diberikan, identifikasi dengan rapi:\n"
    "1. Setiap action item (apa yang harus dikerjakan, satu kalimat).\n"
    "2. Owner (siapa yang bertanggung jawab) — kosongkan jika tidak disebut.\n"
    "3. Deadline (kapan harus selesai) — kosongkan jika tidak disebut.\n"
    "4. Priority — tebak dari konteks: urgent / high / medium / low.\n\n"
    "Aturan output WAJIB:\n"
    "- Bahasa Indonesia, ringkas, tanpa filler.\n"
    "- Jangan mengarang owner/deadline yang tidak tertulis.\n"
    "- Maks 10 action items (pilih yang paling penting).\n"
    "- Format output PERSIS seperti ini, tanpa markdown extra:\n\n"
    "ACTION_ITEMS:\n"
    "- [priority] judul action item | owner | deadline\n"
    "- [priority] judul action item | owner | deadline\n"
    "DECISIONS:\n"
    "- keputusan yang diambil\n"
    "- keputusan lain\n"
    "NEXT_STEPS:\n"
    "- langkah selanjutnya\n"
    "SUMMARY: satu kalimat ringkasan meeting (maks 20 kata)\n\n"
    "Kalau section kosong, tulis '- (none)'. Kalau transkrip bukan meeting "
    "(misal monolog atau curhat), kembalikan SUMMARY saja dengan keterangan "
    "'bukan catatan meeting'."
)

_PRIORITY_RE = re.compile(r"^\[(urgent|high|medium|low)\]\s*", re.IGNORECASE)
_VALID_PRIORITIES = {"urgent", "high", "medium", "low"}
_TASK_PRIORITY_MAP = {"urgent": "urgent", "high": "high", "medium": "medium", "low": "low"}

_MAX_TRANSCRIPT_CHARS = 12000
_MAX_ACTION_ITEMS = 10


def _parse_action_item(line: str) -> dict[str, str] | None:
    line = line.strip().lstrip("-").strip()
    if not line or line.lower() == "(none)":
        return None

    priority = "medium"
    m = _PRIORITY_RE.match(line)
    if m:
        priority = m.group(1).lower()
        if priority not in _VALID_PRIORITIES:
            priority = "medium"
        line = _PRIORITY_RE.sub("", line, count=1)

    parts = [p.strip() for p in line.split("|")]
    title = parts[0] if parts else ""
    owner = parts[1] if len(parts) > 1 and parts[1] not in ("", "-") else ""
    deadline = parts[2] if len(parts) > 2 and parts[2] not in ("", "-") else ""

    if not title:
        return None
    return {"title": title, "priority": priority, "owner": owner, "deadline": deadline}


def _parse_extraction(response: str) -> dict[str, Any]:
    section = None
    action_items: list[dict[str, str]] = []
    decisions: list[str] = []
    next_steps: list[str] = []
    summary = ""

    for raw_line in response.splitlines():
        stripped = raw_line.strip()
        upper = stripped.upper()

        if upper.startswith("ACTION_ITEMS"):
            section = "action_items"
            continue
        if upper.startswith("DECISIONS"):
            section = "decisions"
            continue
        if upper.startswith("NEXT_STEPS"):
            section = "next_steps"
            continue
        if upper.startswith("SUMMARY:"):
            summary = stripped[len("SUMMARY:"):].strip()
            section = None
            continue

        if not stripped or stripped == "-" or stripped.lower() == "- (none)":
            continue

        if section == "action_items":
            item = _parse_action_item(stripped)
            if item and len(action_items) < _MAX_ACTION_ITEMS:
                action_items.append(item)
        elif section == "decisions":
            text = stripped.lstrip("-").strip()
            if text and text.lower() != "(none)":
                decisions.append(text)
        elif section == "next_steps":
            text = stripped.lstrip("-").strip()
            if text and text.lower() != "(none)":
                next_steps.append(text)

    return {
        "action_items": action_items,
        "decisions": decisions,
        "next_steps": next_steps,
        "summary": summary,
    }


async def extract(transcript: str) -> dict[str, Any]:
    if not transcript or not transcript.strip():
        return {"action_items": [], "decisions": [], "next_steps": [], "summary": "transkrip kosong"}

    truncated = transcript[:_MAX_TRANSCRIPT_CHARS]
    was_truncated = len(transcript) > _MAX_TRANSCRIPT_CHARS

    user_content = "Transkrip meeting:\n\n" + truncated
    if was_truncated:
        user_content += f"\n\n... (terpotong, total {len(transcript)} karakter)"

    response = await llm.chat_completion(
        messages=[
            {"role": "system", "content": _EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    parsed = _parse_extraction(response)
    parsed["truncated"] = was_truncated
    parsed["raw"] = response
    return parsed


async def process_meeting(
    transcript: str,
    user_id: str | int | None = None,
    auto_create_tasks: bool = True,
) -> dict[str, Any]:
    extraction = await extract(transcript)
    action_items = extraction["action_items"]

    created_task_ids: list[str] = []
    if auto_create_tasks and action_items:
        for item in action_items:
            title = item["title"]
            if item.get("owner"):
                title = f"{title} (PIC: {item['owner']})"
            try:
                task_id = tools.create_task(
                    title=title,
                    priority=_TASK_PRIORITY_MAP.get(item["priority"], "medium"),
                    due_date=item.get("deadline") or None,
                    user_id=user_id,
                )
                created_task_ids.append(task_id)
            except Exception:
                logger.exception("create_task failed for: %s", title)

    return {
        "action_items": action_items,
        "decisions": extraction["decisions"],
        "next_steps": extraction["next_steps"],
        "summary": extraction["summary"],
        "truncated": extraction["truncated"],
        "tasks_created": len(created_task_ids),
        "task_ids": created_task_ids,
    }


def format_for_telegram(result: dict[str, Any]) -> str:
    lines: list[str] = []
    if result.get("summary"):
        lines.append("📝 <b>Meeting Summary</b>")
        lines.append(result["summary"])
        lines.append("")

    action_items = result.get("action_items") or []
    if action_items:
        lines.append(f"✅ <b>Action Items ({len(action_items)})</b>")
        for item in action_items:
            extras: list[str] = []
            if item.get("owner"):
                extras.append(f"PIC: {item['owner']}")
            if item.get("deadline"):
                extras.append(f"Due: {item['deadline']}")
            tail = f" — {' · '.join(extras)}" if extras else ""
            lines.append(f"• [{item['priority']}] {item['title']}{tail}")
        lines.append("")

    decisions = result.get("decisions") or []
    if decisions:
        lines.append("🎯 <b>Decisions</b>")
        for d in decisions:
            lines.append(f"• {d}")
        lines.append("")

    next_steps = result.get("next_steps") or []
    if next_steps:
        lines.append("➡️ <b>Next Steps</b>")
        for s in next_steps:
            lines.append(f"• {s}")
        lines.append("")

    tasks_created = result.get("tasks_created", 0)
    if tasks_created:
        lines.append(f"💾 {tasks_created} task otomatis dibuat di pending list.")
    elif action_items:
        lines.append("ℹ️ Tasks tidak dibuat otomatis (auto_create_tasks=false).")

    if result.get("truncated"):
        lines.append("")
        lines.append("⚠️ <i>Transkrip terlalu panjang, sebagian dipotong.</i>")

    if not lines:
        return "ℹ️ Tidak ada action item / keputusan terdeteksi dari transkrip."
    return "\n".join(lines).strip()
