import os
from langchain_core.messages import SystemMessage, HumanMessage
from utils.state import AgentState
from utils.models import programmer_llm


def debugger_node(state: AgentState) -> AgentState:
    print("Debugger node: Starting error analysis and code fix")

    system_prompt = """You are an expert Python debugger.
You will be given a Python script that failed and the exact error it produced.
Your only job is to fix the code so it runs without errors.

ABSOLUTE RULES:
- Return ONLY raw Python code. No markdown. No backticks. No explanation.
- First character must be 'i' from 'import'.
- Fix ONLY what is broken — do not rewrite or restructure working sections.
- Do NOT use non-ASCII characters anywhere (no em dashes, curly quotes, etc).
- Every plt.savefig() must be on ONE single line with no line breaks inside.
- No multiline f-strings. Use simple string concatenation for filenames.
- Keep all existing file paths exactly as they are.
- Keep all existing analysis_summary keys and logic intact."""

    human_prompt = f"""The following Python script produced an error when executed.

ERROR:
{state["error"]}

ORIGINAL CODE:
{state["code"]}

Fix the error. Return the complete corrected script.
First character must be 'i' from 'import'."""

    response = programmer_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    fixed_code = response.content.strip()

    if fixed_code.startswith("```"):
        fixed_code = fixed_code.split("```python")[-1].split("```")[0].strip()

    return {
        **state,
        "code": fixed_code,
        "error_count": state.get("error_count", 0) + 1,
        "agent_logs": state.get("agent_logs", "") + f"🔧 Debugger Agent — Fix attempt {state.get('error_count', 0) + 1}/3\n"
    }