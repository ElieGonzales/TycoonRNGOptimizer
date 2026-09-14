import asyncio
import copy
import random
from concurrent.futures import ProcessPoolExecutor
try:
    from . import buildings, definitions
except ImportError:
    import buildings
    import definitions
process_executor = ProcessPoolExecutor()
Timings = [2.5, 1.7, 3.1, 3.6, 2.5, 2.1, 2.5, 2.9, 3.3, 2.9, 2.5, 2.5, 2.4, 2.8, 5.2, 4.2, 1.0]

def get_timings(upgrader_count):
    if upgrader_count <= 0:
        return []
    if upgrader_count > len(Timings):
        raise ValueError(
            f"{upgrader_count} upgraders require at least {upgrader_count} timing values; "
            f"only {len(Timings)} are configured"
        )
    return Timings[-upgrader_count:]

def calculate(droppers, upgraders, processor):
    time_table = get_timings(len(upgraders))
    final_value = 0
    
    for dropper in droppers:
        item = dropper.drop()
        
        for index, upgrader in enumerate(upgraders):
            item = upgrader.upgrade(item)
            item = item.update(time_table[index])
            if item is None or item.value <= 0:
                break
                
        if item is not None and item.value > 0:
            item = processor.process(item)
            final_value += item.value
            
    return final_value


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

def set_rarity(building, rarity):
    building.rarity = rarity

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
                set_rarity(building_obj, rarity)    
                if isinstance(building_obj, buildings.Dropper):
                    available_droppers.append(building_obj)
                elif isinstance(building_obj, buildings.Upgrader):
                    available_upgraders.append(building_obj)
                elif isinstance(building_obj, buildings.Processor):
                    available_processors.append(building_obj)
    return available_droppers, available_upgraders, available_processors, dropper_count, upgrader_count

def _random_candidate(droppers, upgraders, processors, dropper_count, upgrader_count):
    if not processors:
        return None

    return (
        tuple(random.sample(droppers, min(dropper_count, len(droppers)))),
        tuple(random.sample(upgraders, min(upgrader_count, len(upgraders)))),
        random.choice(processors),
    )


def _evaluate(candidate):
    """
    Evaluates a layout candidate. 
    Deepcopy has been removed entirely to achieve massive speedups.
    """
    droppers, upgraders, processor = candidate
    return calculate(droppers, upgraders, processor)


def _mutate(candidate, droppers, upgraders, processors):
    selected_droppers, selected_upgraders, processor = candidate
    selected_droppers = list(selected_droppers)
    selected_upgraders = list(selected_upgraders)

    if selected_droppers and random.random() < 0.35:
        index = random.randrange(len(selected_droppers))
        # Optimized list parsing: compare identities directly using 'is not'
        available = [d for d in droppers if d not in selected_droppers or d is selected_droppers[index]]
        if available:
            selected_droppers[index] = random.choice(available)
            
    if selected_upgraders and random.random() < 0.35:
        index = random.randrange(len(selected_upgraders))
        available = [u for u in upgraders if u not in selected_upgraders or u is selected_upgraders[index]]
        if available:
            selected_upgraders[index] = random.choice(available)
            
    if len(selected_upgraders) > 1 and random.random() < 0.5:
        first, second = random.sample(range(len(selected_upgraders)), 2)
        selected_upgraders[first], selected_upgraders[second] = selected_upgraders[second], selected_upgraders[first]
        
    if random.random() < 0.2:
        processor = random.choice(processors)

    return tuple(selected_droppers), tuple(selected_upgraders), processor

def _describe(candidate, value):
    droppers, upgraders, processor = candidate
    return {
        "droppers": [f"{dropper.rarity} {dropper.name}" for dropper in droppers],
        "upgraders": [f"{upgrader.rarity} {upgrader.name}" for upgrader in upgraders],
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

    loop = asyncio.get_running_loop()

    for generation in range(1, generations + 1):
        # Using loop.run_in_executor alongside ProcessPoolExecutor 
        # successfully offloads tasks across all available CPU cores.
        tasks = [
            loop.run_in_executor(process_executor, _evaluate, candidate) 
            for candidate in population
        ]
        scores = await asyncio.gather(*tasks)
        
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

Presets = {
        "quick": {
            "generations": 100,
            "population_size": 32,
            "elite_size": 4,
            "random_fraction": 0.1,
            "progress_every": 0,
        },
        "balanced": {
            "generations": 500,
            "population_size": 64,
            "elite_size": 8,
            "random_fraction": 0.1,
            "progress_every": 0,
        },
        "explore": {
            "generations": 500,
            "population_size": 128,
            "elite_size": 16,
            "random_fraction": 0.15,
            "progress_every": 0,
        },
        "deep": {
            "generations": 2000,
            "population_size": 128,
            "elite_size": 16,
            "random_fraction": 0.1,
            "progress_every": 0,
        },
    }

def run(path, dropper_count, upgrader_count, preset_name):
    with open(path, "r") as f:
        building_list = f.read()
    droppers, upgraders, processors, dropper_count_from_txt, upgrader_count_from_txt = get_available_buildings(building_list)
    dropper_count = dropper_count_from_txt if dropper_count is None else dropper_count
    upgrader_count = upgrader_count_from_txt if upgrader_count is None else upgrader_count
    preset = Presets[preset_name]
    optimized_buildings = asyncio.run(
        optimize_buildings(
            droppers,
            upgraders,
            processors,
            dropper_count=dropper_count,
            upgrader_count=upgrader_count,
            **preset,
        )
    )
    return optimized_buildings

if __name__ == "__main__":
    AVAILABLE_BUILDINGS_PATH = "available_buildings.txt"
    DROPPER_COUNT = 10
    UPGRADER_COUNT = 17
    ACTIVE_PRESET = "explore"  # Change this to "quick", "balanced", "explore", or "deep" to use different presets
    print(run(AVAILABLE_BUILDINGS_PATH, DROPPER_COUNT, UPGRADER_COUNT, ACTIVE_PRESET))