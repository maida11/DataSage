import os

import os
key = os.getenv("GROQ_API_KEY")
from graph.pipeline import build_graph

def run_pipeline(csv_path: str):

    app = build_graph()

    initial_state = {
    "csv_path": csv_path,
    "column_names": [],
    "sample_rows": "",
    "data_profile": "",
    "plan": "",
    "code": "",
    "error": None,
    "error_count": 0,
    "logs": "",
    "agent_logs": ""
}

    final_state = app.invoke(initial_state)

    

    return final_state

if __name__ == "__main__":
    run_pipeline("data/hr_dataset.csv")