import hashlib
from langgraph.graph import StateGraph, END
from utils.state import AgentState
from utils.ingest import ingest_csv
from utils.compress import compress_plan
from agents.architect import architect_node
from agents.programmer import programmer_node
from agents.executor import executor_node
from agents.debugger import debugger_node

plan_cache = {}

def get_profile_hash(data_profile: str) -> str:
    return hashlib.md5(data_profile.encode()).hexdigest()[:8]

def ingest_node(state: AgentState) -> AgentState:
    result = ingest_csv(state["csv_path"])
    return {
        **state,
        **result,
        "agent_logs": "🔍 Ingest Agent — CSV loaded and profiled\n"
    }

def architect_node_with_cache(state: AgentState) -> AgentState:
    print("Architect node: Checking cache for data profile")
    profile_hash = get_profile_hash(state["data_profile"])
    cache_key = f"{state['csv_path']}_{profile_hash}"

    if cache_key in plan_cache:
        print(" Using cached plan")
        raw_plan = plan_cache[cache_key]
        # Manually append architect log since we skipped architect_node
        architect_log = state.get("agent_logs", "") + "🏗️ Architect Agent — Analysis plan created (cached)\n"
    else:
        result = architect_node(state)
        raw_plan = result["plan"]
        plan_cache[cache_key] = raw_plan
        # Get the log that architect_node appended
        architect_log = result.get("agent_logs", state.get("agent_logs", ""))

    compressed = compress_plan(raw_plan)
    return {**state, "plan": compressed, "agent_logs": architect_log}

def route_after_executor(state: AgentState) -> str:
    
    if state["error"] is None:
        return "end"
    if state["error_count"] >= 3:
        return "end"
    return "debugger"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("ingest", ingest_node)
    graph.add_node("architect", architect_node_with_cache)
    graph.add_node("programmer", programmer_node)
    graph.add_node("executor", executor_node)
    graph.add_node("debugger", debugger_node)

    graph.set_entry_point("ingest")

    graph.add_edge("ingest", "architect")
    graph.add_edge("architect", "programmer")
    graph.add_edge("programmer", "executor")
    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {"end": END, "debugger": "debugger"}
    )
    graph.add_edge("debugger", "executor")

    return graph.compile()