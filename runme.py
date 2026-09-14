import multiprocessing
from src.engine import run


def main():
    path = input("Enter the path to your available buildings file (defaults to available_buildings.txt): ")
    if path == "":
        path = "available_buildings.txt"

    preset_name = input("Enter the optimization preset name (quick, balanced, deep, explore): ")
    if preset_name == "":
        preset_name = "balanced"

    dropper_count = int(input("Enter the number of droppers to use (default 10): "))

    upgrader_count = int(input("Enter the number of upgraders to use (default 17): "))
    print("Calculating...")

    result = run(path, dropper_count, upgrader_count, preset_name)
    print("Optimized buildings:", result)
    with open("optimized_buildings.txt", "w") as f:
        f.write(str(result))
    input("Press Enter to exit...")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()