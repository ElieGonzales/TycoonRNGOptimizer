import multiprocessing

from src.engine import run


def main():
    path = input("Enter the path to your available buildings file (defaults to available_buildings.txt): ")
    if path == "":
        path = "available_buildings.txt"

    preset_name = input("Enter the optimization preset name (quick, balanced, deep, explore): ")
    if preset_name == "":
        preset_name = "balanced"

    dropper_count = input("Enter the number of droppers to use (default 10): ")
    if dropper_count == "":
        dropper_count = 10
    else:
        dropper_count = int(dropper_count)

    upgrader_count = input("Enter the number of upgraders to use (default 17): ")
    if upgrader_count == "":
        upgrader_count = 17
    else:
        upgrader_count = int(upgrader_count)

    result = run(path, dropper_count, upgrader_count, preset_name)
    print("Optimized buildings:", result)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()