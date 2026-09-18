Bonuses = ["Fire", "Wet", "Aired", "Magnetic", "Ancient", "Slimed", "Acid", "Nuclear", "Fueled", "Nebula"]
Destroy_timers = {"Fire": 7.5, "Acid":8.0, "Nuclear":7.5}
Rarities = {"Standard": 1, "Overpowered": 2, "Negative": 3.5, "Hyperspace": 6, "":1, "OP": 2, "N": 3.5, "H": 6}

##TODO: Instead of handling tags, vulns, and raritites as strings, handle them as ints for faster runtime

def apply_rarities(rarities, value):
    for rarity in rarities.split(" "):
        value *= Rarities[rarity]
    return value


class Item:
    def __init__(self, bonuses, effects, vulnerabilities, immunities, value, destroy_timers=None):
        self.bonuses = dict(bonuses)
        self.effects = list(effects)
        self.vulnerabilities = list(vulnerabilities)
        self.immunities = list(immunities)
        self.value = value
        self.destroy_timers = {} if destroy_timers is None else dict(destroy_timers)

    #In between machines: removes effects it's immune to (fallback), applies destroy timers, and applies native bonuses (from the dropper)
    def update(self, time):
        for effect in self.effects:
            if effect in self.immunities:
                self.effects[:] = [active_effect for active_effect in self.effects if active_effect != effect]
                continue
            if effect in Destroy_timers:
                if effect not in self.destroy_timers:
                    self.destroy_timers[effect] = Destroy_timers[effect] - time
                else:
                    self.destroy_timers[effect] -= time
                if self.destroy_timers[effect] <= 0:
                    self.value = 0
            if effect in self.bonuses:
                self.value *= self.bonuses[effect]
                self.bonuses.pop(effect)
        return self


class Dropper:
    def __init__(self, name, eff, rarity="Standard", bonus=None, vulnerabilities=None, immunities=None):
        self.name = name
        self.efficiency = eff
        self.rarity = rarity
        self.bonus = {} if bonus is None else bonus
        self.vulnerabilities = [] if vulnerabilities is None else vulnerabilities
        self.immunities = [] if immunities is None else immunities

    #Returns an Item object with the dropper's bonuses, vulnerabilities, immunities, and value (efficiency * rarity multiplier)
    def drop(self):
        value = apply_rarities(self.rarity, self.efficiency)
        return Item(self.bonus, [], self.vulnerabilities, self.immunities, value)

class Upgrader:
    def __init__(self, name, mult, rarity="Standard", effect_add=None, effect_remove=None, cond_effect_add=None, trans_effect=None, bonuses=None, destroy_chance=0.0):
        self.rarity = rarity
        self.name = name
        self.mult = mult
        self.effect_add = [] if effect_add is None else effect_add
        self.effect_remove = [] if effect_remove is None else effect_remove
        self.cond_effect_add = {} if cond_effect_add is None else cond_effect_add
        self.trans_effect = {} if trans_effect is None else trans_effect
        self.bonuses = {} if bonuses is None else bonuses
        self.destroy_chance = destroy_chance
    def upgrade(self, item):

        #Multiply the item's value by the upgrader's multiplier and apply rarity multiplier
        item.value *= self.mult
        item.value = apply_rarities(self.rarity, item.value)


        #Remove all effects from effect_remove
        if "All" in self.effect_remove:
            removed_effects = set(item.effects)
            item.effects.clear()
            for effect in removed_effects:
                item.destroy_timers.pop(effect, None)
        else:
            removed_effects = set(self.effect_remove).intersection(item.effects)
            item.effects[:] = [effect for effect in item.effects if effect not in self.effect_remove]
            for effect in removed_effects:
                item.destroy_timers.pop(effect, None)

        #Apply bonuses to the item's value if the item has the corresponding effect
        for bonus in self.bonuses:
            if bonus in item.effects:
                item.value *= self.bonuses[bonus]

        #Add effects from effect_add to the item, and add vulnerabilities if the effect starts with "V-"
        for effect in self.effect_add:
            if effect.startswith("V-"):
                item.vulnerabilities.append(effect[2:])
            else:
                item.effects.append(effect)

        #Add conditional effects based on the item's current effects (1 per effect)
        for effect, additions in self.cond_effect_add.items():
            for _ in range(item.effects.count(effect)):
                item.effects.extend(additions)

        #Transform effects based on trans_effect mapping (1 per effect)
        for index, effect in enumerate(item.effects):
            if effect in self.trans_effect:
                item.effects[index] = self.trans_effect[effect]

        #Multiply the item's value by (1 - destroy_chance) to simulate the chance of destruction
        if self.destroy_chance > 0:
            item.value *= (1 - self.destroy_chance)

        return item
        
class Processor:
    def __init__(self, name, mult, rarity="Standard", bonus={}, onlyaccept=[], refuse=[]):
        self.name = name
        self.mult = mult
        self.rarity = rarity
        self.bonus = bonus
        self.onlyaccept = onlyaccept
        self.refuse = refuse

    def process(self, item):

        #If the processor has onlyaccept effects and the item does not have any of those effects, set the item's value to 0
        if self.onlyaccept and not any(effect in item.effects for effect in self.onlyaccept):
            item.value = 0

        #If the processor has refuse effects and the item has any of those effects, set the item's value to 0
        if any(effect in item.effects for effect in self.refuse):
            item.value = 0

        #Multiply the item's value by the processor's multiplier and apply rarity multiplier
        item.value *= self.mult
        item.value = apply_rarities(self.rarity, item.value)

        #Apply bonuses to the item's value if the item has the corresponding effect
        for effect in self.bonus:
            if effect in item.effects:
                item.value *= self.bonus[effect]
        return item