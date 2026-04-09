import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from utils.state import AgentState
from utils.models import programmer_llm

def programmer_node(state: AgentState) -> AgentState:
    print("Programmer node: Starting code generation")
    system_prompt = """You are an expert Python Data Engineer.
Your only job is to translate an analysis plan into a single, complete, runnable Python script.
You are a pure executor. Every decision is already made in the plan.

HARD OUTPUT RULES — READ BEFORE EVERYTHING ELSE:
1. Return ONLY raw Python. No markdown, no backticks.
2. First character must be 'i' from 'import'.
3. NO non-ASCII characters anywhere — no em dashes, no curly quotes.
4. Every plt.savefig() on ONE line. No line breaks inside parentheses.
5. No multiline f-strings. Use simple concatenation for filenames.


═══════════════════════════════════════
SCRIPT STRUCTURE
═══════════════════════════════════════
Your script must follow this structure in order:

1. IMPORTS
   Audit every operation in the plan and import only what is needed.
   Always include: pandas, numpy, matplotlib, seaborn, scipy.stats
   Add any other library only if the plan explicitly requires it.

2. INITIALIZATION
   analysis_summary = {}
   analysis_summary['plots'] = []
   df = pd.read_csv('<csv_path>')
   df_clean = df.copy()

3. PHASES
   Implement every phase from the plan in exact numbered order.
   Every phase must have its OWN try/except block — never group phases together.
   Every sub-phase (4a, 4b, 4c, 4d, 4e) must also have its OWN try/except block.
   Progress print on success, descriptive error print on failure.

4. RESULT STORAGE
   After every major operation store its result in analysis_summary.
   Use descriptive keys derived from the phase, column, and metric.
   Never store placeholder strings — only actual computed values.
   WRONG: analysis_summary['issues'] = 'some string from the plan'
   RIGHT: analysis_summary['quality_col_null_count'] = df['col'].isnull().sum()

5. PLOTTING
   Every plot must:
   - Use fig, ax = plt.subplots() with appropriate figsize
   - Call plt.tight_layout() before saving
   - Save with descriptive filename derived from column names and chart type
   - Call plt.close() after saving
   - Print: [Plot Saved] filename.png
   - Append: analysis_summary['plots'].append('filename.png')
   Never call plt.show().

6. SUMMARY
   Final block loops over analysis_summary and prints every stored result.
   Every recommendation must be derived from actual values stored in analysis_summary.
   Never copy strings from the plan.
   Never hardcode column names or values into recommendation strings.
   Recommendations must be constructed dynamically from whatever was computed and stored.

═══════════════════════════════════════
PHASE-SPECIFIC RULES
═══════════════════════════════════════

PHASE 2 — CLEANING:
- Implement every cleaning decision exactly as the plan states
- After each null fill store: analysis_summary['clean_<col>_null_strategy'] = actual_fill_value
- After outlier flagging store count and values — never remove, only flag
- Outlier bounds: upper = mean + 3*std, lower = mean - 3*std
- Last step of Phase 2 must always be:
  df_clean.to_csv('cleaned_dataset.csv', index=False)
  print("[Cleaned Dataset Saved] cleaned_dataset.csv")

PHASE 3 — TRANSFORMATION:
- Implement only what the plan explicitly states
- Store new column names: analysis_summary['transform_new_columns'] = [list of new cols]

PHASE 4 — EDA:
- Implement only sub-phases the plan marks as  INCLUDED
- Skip any sub-phase marked  SKIPPED — no code, no comment
- Each sub-phase gets its own try/except
- After each analytical result store the computed value in analysis_summary

PHASE 4d — TIME SERIES specifically:
ts = df_clean.groupby(temporal_col)[numeric_col].mean()
ts.index = pd.to_datetime(ts.index)
ts = ts.sort_index()
ts = ts[~ts.index.duplicated(keep='first')]
ts = ts.resample('D').mean().ffill()
- Seasonality detection means running an ADF test — not a line plot
- Rolling averages means computing .rolling(window=N).mean() — not a line plot
- These are three distinct operations producing three distinct outputs
PHASE 5 — SUMMARY:
- Never copy strings from the plan
- Loop over analysis_summary and print all stored computed values
- Derive recommendations from actual stored values only

═══════════════════════════════════════
NULL SAFETY
═══════════════════════════════════════
When operating on multiple columns together always drop nulls row-wise:
df_clean[['col1', 'col2']].dropna()
df_clean['col1'].dropna()                causes length mismatch

═══════════════════════════════════════
OUTPUT RULES — CRITICAL
═══════════════════════════════════════
Return ONLY raw Python code.
Do NOT use markdown.
Do NOT use backticks.
First character must be 'i' from 'import'.
═══════════════════════════════════════
OUTPUT RULES — CRITICAL
═══════════════════════════════════════
Return ONLY raw Python code.
Do NOT use markdown.
Do NOT use backticks.
First character must be 'i' from 'import'.
NEVER use multiline f-strings.
ALL plt.savefig() calls must use simple concatenation only:
  CORRECT: plt.savefig(col + '_histogram.png')
  CORRECT: plt.savefig(f'{col}_histogram.png')
  WRONG:   plt.savefig(f'{
               col}_histogram.png')
Every plt.savefig() must be on a single line with no line breaks inside the string."""

    human_prompt =f"""Here is the complete analysis plan:

{state["plan"]}

IMPORTANT PATH RULES:
- The CSV is located at: /sandbox/data/{os.path.basename(state["csv_path"])}
- Save all plots to current directory (working dir is /sandbox/outputs/)
- Save cleaned CSV as: cleaned_dataset.csv

Translate every numbered step into code exactly as the plan describes.
First character must be 'i' from 'import'."""

    response = programmer_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])

    code = response.content.strip()

    if code.startswith("```"):
        code = code.split("```python")[-1].split("```")[0].strip()

    return {
    **state,
    "code": code,
    "agent_logs": state.get("agent_logs", "") + "💻 Programmer Agent — Python script generated\n"
}