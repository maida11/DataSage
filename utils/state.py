from typing import TypedDict, Optional

class AgentState(TypedDict):
    csv_path: str
    column_names: list[str]
    sample_rows: str
    data_profile: str
    plan: str
    code: str
    error: Optional[str]
    error_count: int
    logs: str
    agent_logs: str