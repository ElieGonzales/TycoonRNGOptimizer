from pyscript import document # type: ignore
from pyodide.ffi import create_proxy # type: ignore
from engine import run
import sys

def throw_exception(exc_type, exc_value, exc_traceback):
    error_msg = f"Error: {exc_value}\n"
    document.getElementById("error-message").innerText = error_msg
    document.getElementById("run-button").innerText = "Run Optimization"
    document.getElementById("run-button").disabled = False

sys.excepthook = throw_exception

async def process_input(event):
    document.getElementById("run-button").innerText = "Running..."
    document.getElementById("run-button").disabled = True

    file_input = document.getElementById("available-buildings")
    if file_input.files.length == 0:
        file_content = document.getElementById("available-buildings-type").value
    else:
        #bruh
        js_buffer = await file_input.files[0].arrayBuffer()
        file_content = js_buffer.to_bytes().decode('utf-8')

    runs = document.getElementById("runs").value
    upgrader_count = document.getElementById("upgrader-count").value 
    dropper_count = document.getElementById("dropper-count").value

    if runs == "":
        runs = 5
    if upgrader_count == "":
        upgrader_count = 0
    if dropper_count == "":
        dropper_count = 0

    print(f"Input values: {file_content}, {dropper_count}, {upgrader_count}, {runs}")

    document.getElementById("error-message").innerText = ""
    results = run(file_content, int(dropper_count), int(upgrader_count), int(runs), verify_final_run=False, web=True)
    print(results.items())
    document.getElementById("value").innerText = results["value"]
    document.getElementById("droppers").innerText = '\n'.join(results["droppers"])
    document.getElementById("upgraders").innerText = '\n↓\n'.join(results["upgraders"])
    document.getElementById("processor").innerText = results["processor"]

    document.getElementById("run-button").innerText = "Done!"
    document.getElementById("run-button").disabled = False

def init():
    run_button = document.getElementById("run-button")
    run_button.addEventListener("click", create_proxy(process_input))

init()