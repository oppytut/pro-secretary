from __future__ import annotations

import re
from typing import Any, TypedDict, cast

from langgraph.graph import END, StateGraph

from . import llm, tools


class AgentState(TypedDict, total=False):
    user_message: str
    user_id: str
    model: str | None
    intent: str
    delete_targets: list[str]
    context_snippets: list[str]
    tool_result: dict[str, Any]
    response: str


_DELETE_VERBS = ("hapus", "delete", "remove", "buang")


_QUOTED_RE = re.compile(r'"([^"]+)"|\u201c([^\u201d]+)\u201d|\u2018([^\u2019]+)\u2019')

_PRIO_PREFIX_RE = re.compile(r"^\s*\[(high|medium|low|urgent)\]\s*", re.IGNORECASE)


def _extract_quoted_targets(message: str) -> list[str]:
    raw: list[str] = []
    for m in _QUOTED_RE.finditer(message):
        for grp in m.groups():
            if grp:
                raw.append(grp)
                break
    cleaned: list[str] = []
    for r in raw:
        stripped = _PRIO_PREFIX_RE.sub("", r).strip()
        if stripped:
            cleaned.append(stripped)
    return cleaned


def understand(state: AgentState) -> AgentState:
    msg = cast(str, state.get("user_message", ""))
    msg_lower = msg.lower().strip()

    if any(verb in msg_lower for verb in _DELETE_VERBS):
        targets = _extract_quoted_targets(msg)
        if targets:
            state["intent"] = "delete_task"
            state["delete_targets"] = targets
            return state

    state["intent"] = "chat"
    return state


def _route_after_understand(state: AgentState) -> str:
    return "delete_task" if state.get("intent") == "delete_task" else "retrieve_context"


def delete_task_node(state: AgentState) -> AgentState:
    targets = state.get("delete_targets") or []
    if not targets:
        state["response"] = "⚠️ Tidak ada target hapus yang terdeteksi."
        return state

    deleted: list[str] = []
    not_found: list[str] = []
    ambiguous: list[tuple[str, int]] = []
    queued_ids: list[str] = []

    for target in targets:
        matches = tools.find_pending_tasks_by_title(target)
        if not matches:
            not_found.append(target)
            continue
        if len(matches) > 1:
            exact = [
                m for m in matches
                if (m.get("payload", {}).get("title") or "").strip().lower() == target.strip().lower()
            ]
            if len(exact) == 1:
                matches = exact
            else:
                ambiguous.append((target, len(matches)))
                continue
        match = matches[0]
        queued_ids.append(match["id"])
        deleted.append(match.get("payload", {}).get("title") or "?")

    deleted_count = 0
    if queued_ids:
        try:
            deleted_count = tools.delete_tasks(queued_ids)
        except Exception as exc:
            state["response"] = f"⚠️ Gagal menghapus task: {exc}"
            return state

    lines: list[str] = []
    if deleted_count > 0:
        lines.append(f"✅ {deleted_count} task dihapus:")
        for title in deleted:
            lines.append(f"• {title}")
    if not_found:
        if lines:
            lines.append("")
        lines.append("⚠️ Tidak ditemukan (mungkin sudah terhapus atau status bukan pending):")
        for t in not_found:
            lines.append(f"• {t}")
    if ambiguous:
        if lines:
            lines.append("")
        lines.append("⚠️ Ambigu (ada beberapa task cocok, butuh judul lebih spesifik):")
        for t, n in ambiguous:
            lines.append(f"• {t} ({n} kandidat)")

    state["response"] = "\n".join(lines) if lines else "⚠️ Tidak ada perubahan."

    try:
        _ = tools.store_memory(
            f"User: {state.get('user_message', '')}\nAssistant: {state['response']}",
            meta={"user_id": state.get("user_id", ""), "action": "delete_task"},
        )
    except Exception:
        pass

    return state


def retrieve_context(state: AgentState) -> AgentState:
    query = cast(str, state.get("user_message", ""))
    snippets: list[str] = []

    try:
        memory_hits = tools.search_memory(query, limit=3)
        for h in memory_hits:
            content = h["payload"].get("content")
            if content:
                snippets.append(f"[memory] {content[:200]}")
    except Exception:
        pass

    try:
        knowledge_hits = tools.search_knowledge(query, limit=3)
        for h in knowledge_hits:
            payload = h["payload"]
            content = payload.get("content", "")
            source = payload.get("source_file") or payload.get("source") or "unknown"
            if content:
                snippets.append(f"[knowledge:{source}] {content[:200]}")
    except Exception:
        pass

    state["context_snippets"] = snippets
    return state


async def generate_response(state: AgentState) -> AgentState:
    user_message = cast(str, state.get("user_message", ""))
    try:
        reply = await llm.chat_with_persona(
            user_message=user_message,
            context_snippets=state.get("context_snippets"),
            model=state.get("model"),
        )
    except Exception as exc:
        reply = f"⚠️ LLM error: {exc}"

    state["response"] = reply

    try:
        _ = tools.store_memory(
            f"User: {user_message}\nAssistant: {reply}",
            meta={"user_id": state.get("user_id", "")},
        )
    except Exception:
        pass

    return state


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("understand", understand)
    graph.add_node("delete_task", delete_task_node)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_response", generate_response)

    graph.set_entry_point("understand")
    graph.add_conditional_edges(
        "understand",
        _route_after_understand,
        {"delete_task": "delete_task", "retrieve_context": "retrieve_context"},
    )
    graph.add_edge("delete_task", END)
    graph.add_edge("retrieve_context", "generate_response")
    graph.add_edge("generate_response", END)
    return graph.compile()


_compiled = None


def get_graph():
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled


async def run_chat(user_message: str, user_id: str, model: str | None = None) -> str:
    graph = get_graph()
    result = await graph.ainvoke(
        {"user_message": user_message, "user_id": user_id, "model": model}
    )
    return result.get("response", "")
