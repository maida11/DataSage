import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from utils.state import AgentState
from utils.models import debugger_llm

def debugger_node(state: AgentState) -> AgentState:
    print(f"Debugger node: Attempt {state['error_count'] + 1} with error:\n{state['error']}\n")
    if state["error_count"] >= 3:
        return {**state, "error": None}

    # Extract only error lines from stdout — strip noise
    relevant_logs = "\n".join(
        line for line in state["logs"].splitlines()
        if line.startswith("Error")
    )

    system_prompt = """You are an expert Python Debugger.
Fix the error in the script and return the complete corrected script.

ABSOLUTE RULES:
- Return the COMPLETE corrected script — not just the fixed section
- Do NOT change any logic, analysis steps, or decisions
- Do NOT add or remove any steps
- Fix only what the error explicitly indicates

COMMON ERROR PATTERNS:
IMPORT ERROR → correct the import at top. adfuller belongs to statsmodels.tsa.stattools NOT scipy.stats
TYPE ERROR → cast to correct type before operation
KEY ERROR → initialize the key before accessing
LENGTH MISMATCH → use row-wise dropna on combined subset
DATETIME/FREQUENCY ERROR with missing values after resample:
- After ts.resample('D').mean(), always forward fill gaps:
  ts = ts.resample('D').mean().ffill()
- Never use dropna() on a resampled time series — it removes the frequency
DUPLICATE LABEL ERROR → use df.loc[~df.index.duplicated(keep='first')] before reindexing
CONVERGENCE ERROR → add guard check, skip gracefully if requirements not met

OUTPUT RULES:
Return ONLY raw Python code.
No markdown. No backticks.
First character must be 'i' from 'import'."""

    human_prompt = f"""Script:
{state["code"]}

Error:
{state["error"]}

Failed operations from stdout:
{relevant_logs if relevant_logs else "No inline errors captured"}

Fix only the error. Return complete corrected script.
First character must be 'i' from 'import'."""

    response = debugger_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    fixed_code = response.content.strip()

    if fixed_code.startswith("```"):
        fixed_code = fixed_code.split("```python")[-1].split("```")[0].strip()


    return {
        **state,
        "code": fixed_code,
        "error": None,
        "error_count": state["error_count"] + 1,
        "agent_logs": state.get("agent_logs", "") + "🔧 Debugger Agent — Fixing error and retrying\n"
    }
