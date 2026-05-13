from __future__ import annotations

from typing import Any, TypedDict, cast

from langgraph.graph import END, StateGraph

from . import llm, tools


class AgentState(TypedDict, total=False):
    user_message: str
    user_id: str
    model: str | None
    intent: str
    context_snippets: list[str]
    tool_result: dict[str, Any]
    response: str


_INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "search": ("cari", "search", "find", "temukan"),
    "task": ("buatkan task", "tambah task", "task:"),
    "note": ("catat", "note:", "simpan note"),
    "schedule": ("jadwal", "schedule", "meeting hari ini", "today's meeting"),
}


def understand(state: AgentState) -> AgentState:
    msg = cast(str, state.get("user_message", "")).lower().strip()
    intent = "chat"
    for candidate, keywords in _INTENT_KEYWORDS.items():
        if any(k in msg for k in keywords):
            intent = candidate
            break
    state["intent"] = intent
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
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_response", generate_response)

    graph.set_entry_point("understand")
    graph.add_edge("understand", "retrieve_context")
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
