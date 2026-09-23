from pyscript import document # type: ignore
from pyodide.ffi import create_proxy # type: ignore
from js import Blob, URL, document as js_document # type: ignore
import definitions
import buildings
import sys

selected_rarities = []
preview_lines = []

def throw_exception(exc_type, exc_value, exc_traceback):
    document.getElementById("error-message").innerText = f"Error: {exc_value}"
    document.getElementById("export-button").disabled = False
sys.excepthook = throw_exception

selected_building = None

def clear_building_selection():
    global selected_building
    if selected_building is not None:
        selected_building[1].classList.remove("selected")
    selected_building = None


def select_building(building, button):
    global selected_building
    clear_building_selection()
    selected_building = (building, button)
    button.classList.add("selected")

def select_rarity(rarity, button):
    if rarity in selected_rarities:
        selected_rarities.remove(rarity)
        button.classList.remove("selected")
    else:
        selected_rarities.append(rarity)
        button.classList.add("selected")


def render_preview(event=None):
    preview = document.getElementById("preview")
    preview.innerText = "\n".join(preview_lines) or "No buildings added yet."
    document.getElementById("export-button").disabled = not preview_lines


def add_buildings(event):
    amount = int(document.getElementById("amount").value or 1)
    if selected_building is not None:
        rarity = " ".join(selected_rarities) or "Standard"
        batch = f"{rarity} - {selected_building[0].name}\n" * amount
    
    if not batch:
        raise ValueError("Select at least one building before adding.")
    else:
        document.getElementById("error-message").innerText = ""
    preview_lines.append(batch)
    clear_building_selection()
    selected_rarities.clear()
    for button in document.querySelectorAll(".rarity-button.selected"):
        button.classList.remove("selected")
    document.getElementById("amount").value = 1
    render_preview()


def export_buildings(event):
    #bruh
    blob = Blob.new(["\n".join(preview_lines) + "\n"], {"type": "text/plain;charset=utf-8"})
    download_url = URL.createObjectURL(blob)
    link = js_document.createElement("a")
    link.href = download_url
    link.download = "available_buildings.txt"
    link.click()
    URL.revokeObjectURL(download_url)

def init():
    for category, buildings_list in (
        ("droppers", definitions.Droppers),
        ("upgraders", definitions.Upgraders),
        ("processors", definitions.Processors),
    ):
        row = document.getElementById(f"{category}-row")
        for building in buildings_list:
            button = document.createElement("button")
            button.innerText = building.name
            button.className = "building-button"
            button.addEventListener("click", create_proxy(
                lambda event, item=building, item_button=button: select_building(
                    item, item_button
                )
            ))
            row.appendChild(button)

    rarities = list(buildings.Rarities.keys())
    rarities_verbose = rarities[1:len(rarities)//2]
    for rarity in rarities_verbose:
        button = document.createElement("button")
        button.innerText = rarity
        button.className = "rarity-button"
        button.addEventListener("click", create_proxy(
            lambda event, value=rarity: select_rarity(value, event.currentTarget)
        ))
        document.getElementById("rarities-row").appendChild(button)

    document.getElementById("add-button").addEventListener("click", create_proxy(add_buildings))
    document.getElementById("export-button").addEventListener("click", create_proxy(export_buildings))
    render_preview()

init()