import multiprocessing
from src.rngoptimizer.engine import *

def main():
    path = input("Enter the path to your available buildings file (defaults to available_buildings.txt): ")
    if path == "":
        path = "available_buildings.txt"


    runs = input("Enter the number of runs (default 10): ")
    runs = 10 if runs == "" else int(runs)

    dropper_count = input("Enter the number of droppers (default from file): ")
    if dropper_count == "":
        dropper_count = 0
    else:
        dropper_count = int(dropper_count)

    upgrader_count = input("Enter the number of upgraders (default from file): ")
    if upgrader_count == "":
        upgrader_count = 0
    else:
        upgrader_count = int(upgrader_count)

    print("Calculating...")

    result = run(path, dropper_count, upgrader_count, runs, verify_final_run=False)
    print("Optimized buildings:", result)
    with open("optimized_buildings.txt", "w") as f:
        for category, buildings in result.items():
            f.write(f"{category}:\n")
            if category == "value":
                f.write(f"  {buildings}\n")
                continue
            if category == "processor":
                f.write(f"  {buildings}\n")
                continue
            for building in buildings:
                f.write(f"  {building}\n")
    input("Press Enter to exit...")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()