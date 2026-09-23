import asyncio
import copy
import os
import random
import math
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
try:
    from . import buildings
except ImportError:
    import buildings
try:
    from . import definitions
except ImportError:
    import definitions
import sys
import traceback

#allows to see the traceback of an exception before the program exits
def show_exception_and_exit(exc_type, exc_value, tb):
    traceback.print_exception(exc_type, exc_value, tb)
    input("\nPress Enter to exit...")
    sys.exit(-1)

sys.excepthook = show_exception_and_exit


#Gets the time between upgraders for destruction effects
def get_timings(upgrader_count):
    timings = [2.5, 1.7, 3.1, 3.6, 2.5, 2.1, 2.5, 2.9, 3.3, 2.9, 2.5, 2.5, 2.4, 2.8, 5.2, 4.2, 1.0]
    if upgrader_count <= 0:
        return []
    return timings[-upgrader_count:]

#Evaluates the estimated revenue/sec of a given layout
def calculate_factory(droppers, upgraders, processor, verbose=False, super_verbose=False):
    time_table = get_timings(len(upgraders))
    final_value = 0
    if super_verbose:
        verbose = True
    
    for dropper in droppers:
        item = dropper.drop(verbose=verbose, super_verbose=super_verbose)
        
        for step, upgrader in enumerate(upgraders):
            item = upgrader.upgrade(item, super_verbose=super_verbose)
            item = item.update(time_table[step], verbose=verbose, super_verbose=super_verbose)
            if item is None or item.value <= 0:
                if verbose:
                    print(f"Item destroyed after {step + 1} upgraders.")
                break
                
        if item is not None and item.value > 0:
            item = processor.process(item, verbose=verbose, super_verbose=super_verbose)
            final_value += item.value
    if super_verbose:
        print(f"Final value: {final_value}")
        print(f"Last item effects: {item.effects if item is not None else 'N/A'}")
    return final_value

#Returns the building object based on the name of the building
def get_building_by_name(name):
    for dropper in definitions.Droppers:
        if dropper.name.lower() == name.lower().strip():
            return dropper
    for upgrader in definitions.Upgraders:
        if upgrader.name.lower() == name.lower().strip():
            return upgrader
    for processor in definitions.Processors:
        if processor.name.lower() == name.lower().strip():
            return processor
    return None

#Gets buildings from raw text
def get_available_buildings(building_list, web=False):
    #Words before - are the rarities
    #Words after - is the building name
    #\ns are the building list
    available_droppers = []
    available_upgraders = []
    available_processors = []
    dropper_count = 10
    upgrader_count = 17
    for building in building_list.split("\n"):
        if building.startswith("#"):
            continue
        if building.startswith("@"):
            count = building.split(" ")[-1]
            if building.startswith("@Dr"):
                dropper_count = int(count)
            elif building.startswith("@Up"):
                upgrader_count = int(count)
        building = building.strip()
        if building:
            parts = building.split("-")
            if len(parts) == 2:
                rarity, name = (part.strip() for part in parts)
            else:
                rarity = "Standard"
                name = parts[0].strip()
            building_obj = get_building_by_name(name)
            if building_obj:
                building_obj = copy.deepcopy(building_obj)
                rarities = []
                for r in rarity.split(" "):
                    r = r.strip()
                    if len(r) < 3:
                        r = r.upper()
                    else:
                        r = r.title()
                    rarities.append(r)
                building_obj.rarity = " ".join(rarities)
                if isinstance(building_obj, buildings.Dropper):
                    available_droppers.append(building_obj)
                elif isinstance(building_obj, buildings.Upgrader):
                    available_upgraders.append(building_obj)
                elif isinstance(building_obj, buildings.Processor):
                    available_processors.append(building_obj)
            elif not building.startswith("@"):
                if not web:
                    print(f"Warning: Building '{name.title()}' not found in definitions.")
                else:
                    raise ValueError(f"Building '{name.title()}' not found in definitions.")
    return available_droppers, available_upgraders, available_processors, dropper_count, upgrader_count


#---GENETIC ALGORITHM---

def _random_candidate(droppers, upgraders, processors, dropper_count, upgrader_count):
    if not processors:
        return None

    return (
        tuple(random.sample(droppers, min(dropper_count, len(droppers)))),
        tuple(random.sample(upgraders, min(upgrader_count, len(upgraders)))),
        random.choice(processors),
    )

def _evaluate(candidate):
    droppers, upgraders, processor = candidate
    return calculate_factory(droppers, upgraders, processor)

def _evaluate_batch(candidates):
    return [_evaluate(candidate) for candidate in candidates]

def _mutate(candidate, droppers, upgraders, processors):
    selected_droppers, selected_upgraders, processor = candidate
    selected_droppers = list(selected_droppers)
    selected_upgraders = list(selected_upgraders)

    if selected_droppers and random.random() < 0.35:
        index = random.randrange(len(selected_droppers))
        available = [
            dropper
            for dropper in droppers
            if dropper not in selected_droppers or dropper is selected_droppers[index]
        ]
        if available:
            selected_droppers[index] = random.choice(available)
            
    if selected_upgraders and random.random() < 0.35:
        index = random.randrange(len(selected_upgraders))
        available = [
            upgrader
            for upgrader in upgraders
            if upgrader not in selected_upgraders or upgrader is selected_upgraders[index]
        ]
        if available:
            selected_upgraders[index] = random.choice(available)
            
    if len(selected_upgraders) > 1 and random.random() < 0.5:
        first, second = random.sample(range(len(selected_upgraders)), 2)
        selected_upgraders[first], selected_upgraders[second] = selected_upgraders[second], selected_upgraders[first]
        
    if random.random() < 0.2:
        processor = random.choice(processors)

    return tuple(selected_droppers), tuple(selected_upgraders), processor

def _describe(candidate, value):
    selected_droppers, selected_upgraders, processor = candidate

    if value == 0:
        value = "0"
    else:
        suffixes = ["", "K", "M", "B", "T",
        "Qa", "Qi", "Sx", "Sp", "Oc",
        "No", "Dc", "Ud", "Dd", "Td",
        "Qad", "Qid", "Sxd", "Spd", "Ocd",
        "Nod", "Vg", "Uvg", "Dvg", "Tvg",
        "Qavg", "Qivg", "Sxvg", "Spvg", "Ocvg",
        "Novg", "Tg", "Utg", "Dtg", "Ttg",
        "Qatg", "Qitg", "Sxtg", "Sptg", "Octg",
        "Notg", "Qag", "Uqag", "Dqag", "Tqag"]
        magnitude = int(math.floor(math.log10(abs(value)) / 3)) if value != 0 else 0
        
        if magnitude >= len(suffixes):
            value = f"{value:.{3}e}"
        else:
            scaled_value = value / (10 ** (magnitude * 3))
            value = f"{scaled_value:.{3}f} {suffixes[magnitude]}"

    return {
        "droppers": [
            f"{dropper.rarity} {dropper.name}"
            for dropper in selected_droppers
        ],
        "upgraders": [
            f"{upgrader.rarity} {upgrader.name}"
            for upgrader in selected_upgraders
        ],
        "processor": f"{processor.rarity} {processor.name}",
        "value": value,
    }

async def optimize_buildings(
    droppers,
    upgraders,
    processors,
    dropper_count=None,
    upgrader_count=None,
    generations=100,
    population_size=64,
    elite_size=8,
    seed=None,
    random_fraction=0.1,
    stagnation_patience=10,
    max_random_fraction=0.5,
    progress_every=None,
    target_value=None,
    web=False,
):
    if not droppers or not upgraders or not processors:
        raise ValueError("at least one dropper, upgrader, and processor is required")
    if dropper_count is None:
        dropper_count = len(droppers)
    if upgrader_count is None:
        upgrader_count = len(upgraders)
    if not 0 <= random_fraction <= 1:
        raise ValueError("random_fraction must be between 0 and 1")
    if stagnation_patience < 1:
        raise ValueError("stagnation_patience must be positive")
    if not random_fraction <= max_random_fraction <= 1:
        raise ValueError("max_random_fraction must be between random_fraction and 1")
    if seed is not None:
        random.seed(seed)

    population = [
        _random_candidate(droppers, upgraders, processors, dropper_count, upgrader_count)
        for _ in range(max(population_size, elite_size))
    ]
    best_candidate = None
    best_value = float("-inf")
    stagnant_generations = 0
    immigrant_fraction = random_fraction
    score_cache = {}

    loop = asyncio.get_running_loop()
    if web:
        executor = ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 1))
        worker_count_limit = min(4, os.cpu_count() or 1)
    else:
        executor = ProcessPoolExecutor()
        worker_count_limit = os.cpu_count() or 1

    with executor as process_executor:
        for generation in range(1, generations + 1):
            uncached_candidates = list(dict.fromkeys(population))
            uncached_candidates = [
                candidate for candidate in uncached_candidates
                if candidate not in score_cache
            ]
            if uncached_candidates:
                worker_count = min(len(uncached_candidates), worker_count_limit)
                chunk_size = max(
                    1,
                    (len(uncached_candidates) + worker_count - 1) // worker_count
                    if web else
                    (len(uncached_candidates) + worker_count * 2 - 1)
                    // (worker_count * 2),
                )
                candidate_batches = [
                    uncached_candidates[start:start + chunk_size]
                    for start in range(0, len(uncached_candidates), chunk_size)
                ]
                tasks = [
                    loop.run_in_executor(process_executor, _evaluate_batch, batch)
                    for batch in candidate_batches
                ]
                score_batches = await asyncio.gather(*tasks)
                uncached_scores = [score for batch in score_batches for score in batch]
                score_cache.update(zip(uncached_candidates, uncached_scores))

            scores = [score_cache[candidate] for candidate in population]
        
            ranked = sorted(zip(scores, population), key=lambda result: result[0], reverse=True)
            if ranked[0][0] > best_value:
                best_value, best_candidate = ranked[0]
                stagnant_generations = 0
                immigrant_fraction = random_fraction
            else:
                stagnant_generations += 1
                if stagnant_generations >= stagnation_patience:
                    immigrant_fraction = min(max_random_fraction, immigrant_fraction + 0.1)

            if progress_every and (generation % progress_every == 0 or generation == 1):
                print(
                    f"Generation {generation}: best value = {best_value} "
                    f"(immigrants: {immigrant_fraction:.0%})"
                )
                print(_describe(best_candidate, best_value))
            
            if target_value is not None and best_value >= target_value:
                break

            elites = [candidate for _, candidate in ranked[:max(1, elite_size)]]
            population = elites[:]
        
            while len(population) < population_size:
                if random.random() < immigrant_fraction:
                    population.append(
                        _random_candidate(droppers, upgraders, processors, dropper_count, upgrader_count)
                    )
                else:
                    parent = random.choice(elites)
                    population.append(_mutate(parent, droppers, upgraders, processors))
                
            await asyncio.sleep(0)

    return best_candidate, best_value

#----------//-----------


#Runs the optimization process with the given parameters and returns the best result
def run(path, dropper_count, upgrader_count, runs=10, run_stagnation_patience=10, verify_final_run=True, web=False):
    if not web:
        with open(path, "r") as f:
            building_list = f.read()
    else:
        building_list = path
    droppers, upgraders, processors, dropper_count_from_txt, upgrader_count_from_txt = get_available_buildings(building_list, web=web)
    if not droppers or not upgraders or not processors:
        raise ValueError(
            "available buildings must contain at least one dropper, upgrader, and processor"
        )
    dropper_count = dropper_count_from_txt if dropper_count == 0 else int(dropper_count)
    upgrader_count = upgrader_count_from_txt if upgrader_count == 0 else int(upgrader_count)

    runs = abs(int(runs))
    if run_stagnation_patience < 1:
        raise ValueError("run_stagnation_patience must be positive")

    best_result = None
    stagnant_runs = 0
    for run_number in range(1, runs + 1):
        best_candidate, value = asyncio.run(
            optimize_buildings(
                droppers,
                upgraders,
                processors,
                dropper_count=dropper_count,
                upgrader_count=upgrader_count,
                generations=150,
                population_size=64,
                elite_size=8,
                random_fraction=0.1,
                progress_every=0,
                stagnation_patience=run_stagnation_patience,
                web=web,
            )
        )
        if best_result is None or value > best_result["value"]:
            best_result = {"candidate": best_candidate, "value": value}
            stagnant_runs = 0
        else:
            stagnant_runs += 1
        print(f"Run {run_number}/{runs}: {value} (best: {best_result['value']})")
        if stagnant_runs >= run_stagnation_patience:
            print(f"Stopping after {stagnant_runs} runs without improvement.")
            break

    if verify_final_run:
        print('Verifying final run...')
        calculate_factory(*best_result["candidate"], verbose=True)
    return _describe(best_result["candidate"], best_result["value"])

if __name__ == "__main__":
    AVAILABLE_BUILDINGS_PATH = "available_buildings.txt"
    DROPPER_COUNT = 5
    UPGRADER_COUNT = 7
    RUNS = 20
    print(run(AVAILABLE_BUILDINGS_PATH, DROPPER_COUNT, UPGRADER_COUNT, RUNS))