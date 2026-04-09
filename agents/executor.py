import docker
import os
import glob
import re
import uuid
import shutil
from utils.state import AgentState

client = docker.from_env()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ERROR_PREFIXES = (
    "Error ",
    "Traceback",
    "SyntaxError",
    "TypeError",
    "ValueError",
    "KeyError",
    "IndexError",
    "AttributeError",
    "NameError",
    "ImportError",
    "ModuleNotFoundError",
    "RuntimeError",
    "ZeroDivisionError",
    "FileNotFoundError",
)


def sanitize_code(code: str) -> str:
    # Strip BOM and normalize line endings
    code = code.replace('\r\n', '\n').replace('\r', '\n').lstrip('\ufeff')

    # Kill all non-ASCII characters (em dashes, curly quotes, etc.)
    code = ''.join(
        c if ord(c) < 128 else ' '
        for c in code
    )

    # Join broken savefig lines — catches LLM line-wrapping inside strings
    code = re.sub(
        r'plt\.savefig\(([^)]*)\n([^)]*)\)',
        lambda m: f"plt.savefig({(m.group(1) + m.group(2)).strip()})",
        code
    )

    # Strip markdown fences if they survived the programmer node
    if '```' in code:
        code = re.sub(r'```(?:python)?\n?', '', code)

    return code


def executor_node(state: AgentState) -> AgentState:
    print("Executor node: Starting code execution")

    outputs_dir = os.path.join(BASE_DIR, "outputs")
    saved_dir = os.path.join(BASE_DIR, "outputs", "saved")
    data_dir = os.path.join(BASE_DIR, "data")
    sandbox_dir = os.path.join(BASE_DIR, "sandbox")

    os.makedirs(sandbox_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(saved_dir, exist_ok=True)

    # On first attempt clear everything including saved, on retry clear only current outputs
    if state["error_count"] == 0:
        for f in glob.glob(os.path.join(outputs_dir, "*.png")):
            os.remove(f)
        for f in glob.glob(os.path.join(saved_dir, "*.png")):
            os.remove(f)
    else:
        for f in glob.glob(os.path.join(outputs_dir, "*.png")):
            os.remove(f)

    code = sanitize_code(state["code"])

    code_filename = f"code_{uuid.uuid4().hex[:8]}.py"
    tmp_path = os.path.join(sandbox_dir, code_filename)

    print(f"Writing code to: {tmp_path}")
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"File written, size: {os.path.getsize(tmp_path)} bytes")

    print("DATA DIR:", data_dir)
    print("OUTPUTS DIR:", outputs_dir)
    print("CODE FILE EXISTS:", os.path.exists(tmp_path))
    print("FILES IN DATA DIR:", os.listdir(data_dir))

    try:
        result = client.containers.run(
            image="datasage-sandbox",
            command=f"python /sandbox/code/{code_filename}",
            volumes={
                sandbox_dir: {"bind": "/sandbox/code", "mode": "ro"},
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
            line.lstrip().startswith(ERROR_PREFIXES)
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
                if line.lstrip().startswith(ERROR_PREFIXES)
            )
            print("\n🔴 INLINE ERROR DETECTED:")
            print(error_msg)
            return {
                **state,
                "logs": stdout,
                "error": error_msg,
                "agent_logs": state.get("agent_logs", "") + "⚙️ Executor Agent — Error detected\n"
            }

    except docker.errors.ContainerError as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else str(e)
        print("\n🔴 CONTAINER ERROR:")
        print(stderr)
        return {
            **state,
            "logs": "",
            "error": stderr,
            "agent_logs": state.get("agent_logs", "") + "⚙️ Executor Agent — Error detected\n"
        }

    except Exception as e:
        print("\n🔴 UNEXPECTED ERROR:")
        print(str(e))
        return {
            **state,
            "logs": "",
            "error": str(e),
            "agent_logs": state.get("agent_logs", "") + "⚙️ Executor Agent — Error detected\n"
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)