
import argparse
from rngoptimizer.engine import run

def main_cli():

    parser = argparse.ArgumentParser(description="Run the building optimization engine.")
    parser.add_argument("-p","--path", type=str, default="available_buildings.txt", help="Path to available buildings file")
    parser.add_argument("-r", "--runs", type=int, default=1, help="Number of runs")
    parser.add_argument("-d", "--droppers", type=int, default=0, help="Number of droppers")
    parser.add_argument("-u", "--upgraders", type=int, default=0, help="Number of upgraders")

    args = parser.parse_args()
    if args.path == "":
        args.path = "available_buildings.txt"
    args.runs = abs(args.runs)
    args.droppers = abs(args.droppers)
    args.upgraders = abs(args.upgraders)

    print("Calculating...")

    result = run(args.path, args.droppers, args.upgraders, args.runs)
    print("Optimized buildings:", result)
    with open("optimized_buildings.txt", "w") as f:
        f.write(str(result))
    input("Press Enter to exit...")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main_cli()