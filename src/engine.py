import asyncio
import copy
import os
import random
from concurrent.futures import ProcessPoolExecutor
try:
    from . import buildings, definitions
except ImportError:
    import buildings
    import definitions

#Gets the time between upgraders for destruction effects
def get_timings(upgrader_count):
    timings = [2.5, 1.7, 3.1, 3.6, 2.5, 2.1, 2.5, 2.9, 3.3, 2.9, 2.5, 2.5, 2.4, 2.8, 5.2, 4.2, 1.0]
    if upgrader_count <= 0:
        return []
    return timings[-upgrader_count:]

#Evaluates the estimated revenue/sec of a given layout
def calculate_factory(droppers, upgraders, processor):
    time_table = get_timings(len(upgraders))
    final_value = 0
    
    for dropper in droppers:
        item = dropper.drop()
        
        for step, upgrader in enumerate(upgraders):
            item = upgrader.upgrade(item)
            item = item.update(time_table[step])
            if item is None or item.value <= 0:
                break
                
        if item is not None and item.value > 0:
            item = processor.process(item)
            final_value += item.value
            
    return final_value

#Returns the building object based on the name of the building
def get_building_by_name(name):
    for dropper in definitions.Droppers:
        if dropper.name == name:
            return dropper
    for upgrader in definitions.Upgraders:
        if upgrader.name == name:
            return upgrader
    for processor in definitions.Processors:
        if processor.name == name:
            return processor
    return None

#Gets buildings from raw text
def get_available_buildings(building_list):
    #Words before - are the rarities
    #Words after - is the building name
    #\ns are the building list
    available_droppers = []
    available_upgraders = []
    available_processors = []
    dropper_count = 0
    upgrader_count = 0
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
                building_obj.rarity = rarity  
                if isinstance(building_obj, buildings.Dropper):
                    available_droppers.append(building_obj)
                elif isinstance(building_obj, buildings.Upgrader):
                    available_upgraders.append(building_obj)
                elif isinstance(building_obj, buildings.Processor):
                    available_processors.append(building_obj)
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
    with ProcessPoolExecutor() as process_executor:
        for generation in range(1, generations + 1):
            uncached_candidates = list(dict.fromkeys(population))
            uncached_candidates = [
                candidate for candidate in uncached_candidates
                if candidate not in score_cache
            ]
            if uncached_candidates:
                worker_count = min(len(uncached_candidates), os.cpu_count() or 1)
                chunk_size = max(
                    1,
                    (len(uncached_candidates) + worker_count * 2 - 1) // (worker_count * 2),
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

    return _describe(best_candidate, best_value)

#----------//-----------


#Runs the optimization process with the given parameters and returns the best result
def run(path, dropper_count, upgrader_count, runs=1, run_stagnation_patience=8):
    with open(path, "r") as f:
        building_list = f.read()
    droppers, upgraders, processors, dropper_count_from_txt, upgrader_count_from_txt = get_available_buildings(building_list)
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
        result = asyncio.run(
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
            )
        )
        if best_result is None or result["value"] > best_result["value"]:
            best_result = result
            stagnant_runs = 0
        else:
            stagnant_runs += 1
        print(f"Run {run_number}/{runs}: {result['value']}")
        if stagnant_runs >= run_stagnation_patience:
            print(f"Stopping after {stagnant_runs} runs without improvement.")
            break

    return best_result

if __name__ == "__main__":
    AVAILABLE_BUILDINGS_PATH = "available_buildings.txt"
    DROPPER_COUNT = 5
    UPGRADER_COUNT = 7
    RUNS = 20
    print(run(AVAILABLE_BUILDINGS_PATH, DROPPER_COUNT, UPGRADER_COUNT, RUNS))