from pyscript import document # type: ignore
from pyodide.ffi import create_proxy # type: ignore
from engine import run

async def process_input(event):
    document.getElementById("run-button").innerText = "Running..."
    document.getElementById("run-button").disabled = True

    file_input = document.getElementById("available-buildings")
    #bruh
    js_buffer = await file_input.files[0].arrayBuffer()
    file_content = js_buffer.to_bytes().decode('utf-8')

    runs = document.getElementById("runs").value or 0
    upgrader_count = document.getElementById("upgrader-count").value or 0
    dropper_count = document.getElementById("dropper-count").value or 0

    print(f"Input values: {file_content}, {dropper_count}, {upgrader_count}, {runs}")

    results = run(file_content, int(dropper_count), int(upgrader_count), int(runs), verify_final_run=False, web=True)
    print(results.items())
    document.getElementById("value").innerText = results["value"]
    document.getElementById("droppers").innerText = '\n '.join(results["droppers"])
    document.getElementById("upgraders").innerText = '\n '.join(results["upgraders"])
    document.getElementById("processor").innerText = results["processor"]

    document.getElementById("run-button").innerText = "Done!"
    document.getElementById("run-button").disabled = False

def init():
    run_button = document.getElementById("run-button")
    run_button.addEventListener("click", create_proxy(process_input))

init()