

import docker
import tempfile
import os
import glob
from utils.state import AgentState
import shutil

client = docker.from_env()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sanitize_code(code: str) -> str:
    """Fix common LLM code generation issues"""
    lines = []
    for line in code.split('\n'):
        stripped = line.rstrip()

        # Fix mixed quotes — opens with " closes with '
        if 'f"' in stripped and stripped.endswith("')"):
            line = stripped[:-2] + '")'

        # Fix mixed quotes — opens with ' closes with "
        elif "f'" in stripped and stripped.endswith('")'):
            line = stripped[:-2] + "')"

        # Fix unterminated print strings — line has print(" but no closing "
        elif stripped.lstrip().startswith('print(') and stripped.count('"') % 2 != 0:
            line = stripped + '")'

        # Fix unterminated print strings with single quotes
        elif stripped.lstrip().startswith('print(') and stripped.count("'") % 2 != 0:
            line = stripped + "')"

        lines.append(line)
    return '\n'.join(lines)


def executor_node(state: AgentState) -> AgentState:
    print("Executor node: Starting code execution")
    # Clear previous plots
    outputs_dir = os.path.join(BASE_DIR, "outputs")
    saved_dir = os.path.join(BASE_DIR, "outputs", "saved")

    # On first attempt, clear everything including saved
    if state["error_count"] == 0:
        for f in glob.glob(os.path.join(outputs_dir, "*.png")):
            os.remove(f)
        os.makedirs(saved_dir, exist_ok=True)
        for f in glob.glob(os.path.join(saved_dir, "*.png")):
            os.remove(f)
        os.makedirs(saved_dir, exist_ok=True)
    else:
        # On retry, clear only current outputs (not saved)
        for f in glob.glob(os.path.join(outputs_dir, "*.png")):
            os.remove(f)

    code = sanitize_code(state["code"])

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.py', delete=False, encoding='utf-8'
    ) as f:
        f.write(code)
        tmp_path = f.name
        tmp_filename = os.path.basename(tmp_path)

    # Resolve absolute paths for Docker volumes
    code_dir = os.path.dirname(os.path.abspath(tmp_path))
    data_dir = os.path.join(BASE_DIR, "data")
    outputs_dir = os.path.join(BASE_DIR, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    print("DATA DIR:", data_dir)
    print("OUTPUTS DIR:", outputs_dir)

    try:
        result = client.containers.run(
            image="datasage-sandbox",
            command=f"python /sandbox/code/{tmp_filename}",
            volumes={
                code_dir: {"bind": "/sandbox/code", "mode": "ro"},
                data_dir: {"bind": "/sandbox/data", "mode": "ro"},
                outputs_dir: {"bind": "/sandbox/outputs", "mode": "rw"},
            },
            working_dir="/sandbox/outputs",
            remove=True,
            stdout=True,
            stderr=True,
        )

        stdout = result.decode("utf-8").strip()

        print("\n STDOUT:")
        print(stdout if stdout else "(empty)")

        has_inline_errors = any(
            line.startswith("Error ")
            for line in stdout.splitlines()
        )

        if not has_inline_errors:
            for f in glob.glob(os.path.join(outputs_dir, "*.png")):
                shutil.copy2(f, saved_dir)
            return {
                **state,
                "logs": stdout,
                "error": None,
                "agent_logs": state.get("agent_logs", "") + "⚙️ Executor Agent — Code ran successfully\n"
            }
        else:
            error_msg = "\n".join(
                line for line in stdout.splitlines()
                if line.startswith("Error ")
            )
            return {
                **state,
                "logs": stdout,
                "error": error_msg,
                "agent_logs": state.get("agent_logs", "") + "⚙️ Executor Agent — Error detected\n"
            }

    except docker.errors.ContainerError as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else str(e)
        return {
            **state,
            "logs": "",
            "error": stderr,
            "agent_logs": state.get("agent_logs", "") + "⚙️ Executor Agent — Error detected\n"
        }

    except Exception as e:
        return {
            **state,
            "logs": "",
            "error": str(e)
        }

    finally:
        os.unlink(tmp_path)