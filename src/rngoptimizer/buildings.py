Bonuses = ["Fire", "Wet", "Aired", "Magnetic", "Ancient", "Slimed", "Acid", "Nuclear", "Fueled", "Nebula"]
Destroy_timers = {"Fire": 7.5, "Acid":8.0, "Nuclear":7.5}
Rarities = {"Standard": 1, "Overpowered": 2, "Negative": 3.5, "Hyperspace": 6, "OP": 2, "N": 3.5, "H": 6}

##TODO: Instead of handling tags, vulns, and raritites as strings, handle them as ints for faster runtime

def apply_rarities(rarities, value):
    for rarity in rarities.split():
        try:
            value *= Rarities[rarity]
        except KeyError:
            supported = ", ".join(Rarities)
            raise ValueError(
                f"Unknown rarity '{rarity}'. Supported rarities: {supported}"
            ) from None
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
    def update(self, time, verbose=False, super_verbose=False):
        if self.value <= 0:
            if super_verbose:
                print(f"Item has value {self.value}, skipping update.")
            return self
    
        #Put vulnerabilities at the end of the list to avoid destroying the item before applying interactions
        self.effects.sort(key=lambda x: x in self.vulnerabilities)
        if super_verbose:
            print(f"Updating item with value {self.value} and effects {self.effects} for {time} seconds.")
        for effect in self.effects:
            if self.value <= 0:
                if super_verbose:
                    print(f"Item has value {self.value}, skipping remaining effects.")
                break

            #Tag interactions:
            if effect == "Fire" and "Wet" in self.effects:
                if super_verbose:
                    print(f"Item has both Fire and Wet effects, removing both.")
                #set to none as to not break the loop, will be removed in the next iteration
                self.effects[self.effects.index("Fire")] = None
                self.effects[self.effects.index("Wet")] = None
                continue
            elif effect == "Wet" and "Fire" in self.effects:
                if super_verbose:
                    print(f"Item has both Wet and Fire effects, removing both.")
                #set to none as to not break the loop, will be removed in the next iteration
                self.effects[self.effects.index("Fire")] = None
                self.effects[self.effects.index("Wet")] = None
                continue

            if effect == "Ice" and "Fire" in self.effects:
                if super_verbose:
                    print(f"Item has both Ice and Fire effects, removing both and adding Wet effect.")
                #set to none as to not break the loop, will be removed in the next iteration
                self.effects[self.effects.index("Fire")] = None
                self.effects[self.effects.index("Ice")] = None
                self.effects.append("Wet")
                continue

            if effect == "Fire" and "Ice" in self.effects:
                if super_verbose:
                    print(f"Item has both Fire and Ice effects, removing both and adding Wet effect.")
                #set to none as to not break the loop, will be removed in the next iteration
                self.effects[self.effects.index("Fire")] = None
                self.effects[self.effects.index("Ice")] = None
                self.effects.append("Wet")
                continue


            #Remove effects that the item is immune to
            if effect in self.immunities:
                if super_verbose:
                    print(f"Item is immune to {effect}, removing effect.")
                self.effects[:] = [active_effect for active_effect in self.effects if active_effect != effect]
                continue

            #Count down destroying effects and destroy the item if the timer reaches 0
            if effect in Destroy_timers:
                if effect not in self.destroy_timers:
                    if super_verbose:
                        print(f"Item has {effect} effect, starting destroy timer.")
                    self.destroy_timers[effect] = Destroy_timers[effect] - time
                else:
                    self.destroy_timers[effect] -= time
                if self.destroy_timers[effect] <= 0:
                    self.value = 0
                    if verbose:
                        print(f"Item destroyed due to {effect} effect.")

            #Destroy the item if it has a vulnerability to an effect it has
            if effect in self.vulnerabilities:
                self.value = 0
                if verbose:
                    print(f"Item destroyed due to {effect} vulnerability.")
        self.effects = [effect for effect in self.effects if effect is not None]  # Remove None effects
            
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
    def drop(self, verbose=False, super_verbose=False):
        if super_verbose:
            print(f"Dropping item from {self.name}")
        if verbose and self.vulnerabilities:
            print(f"Warning: Dropper {self.name} has vulnerabilities: {self.vulnerabilities}")

        
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
    def upgrade(self, item, super_verbose=False):
        if super_verbose:
            print(f"Upgrading item using {self.name}.")

        #Multiply the item's value by the upgrader's multiplier and apply rarity multiplier
        item.value *= self.mult
        item.value = apply_rarities(self.rarity, item.value)

        #get a modifiable copy of the bonuses to avoid repeat applications
        i_bonuses = dict(item.bonuses)


        #Remove all effects from effect_remove
        if "All" in self.effect_remove:
            removed_effects = set(item.effects)
            if super_verbose:
                print(f"Removing all effects from item: {removed_effects}")
            item.effects.clear()
            for effect in removed_effects:
                item.destroy_timers.pop(effect, None)
        else:
            if super_verbose and self.effect_remove:
                print(f"Removing effects from item: {self.effect_remove}")
            removed_effects = set(self.effect_remove).intersection(item.effects)
            item.effects[:] = [effect for effect in item.effects if effect not in self.effect_remove]
            for effect in removed_effects:
                item.destroy_timers.pop(effect, None)

        #Apply bonuses to the item's value if the item has the corresponding effect
        for bonus in self.bonuses:
            if bonus in item.effects:
                if super_verbose:
                    print(f"Applying bonus for effect {bonus}: {self.bonuses[bonus]}")
                item.value *= self.bonuses[bonus]


        #Add effects from effect_add to the item, and add vulnerabilities if the effect starts with "V-"
        for effect in self.effect_add:
            if effect.startswith("V-"):
                if super_verbose:
                    print(f"Adding vulnerability {effect[2:]} to item.")
                item.vulnerabilities.append(effect[2:])
            else:
                if super_verbose:
                    print(f"Adding effect {effect} to item.")
                item.effects.append(effect)
                if effect in i_bonuses:
                    if super_verbose:
                        print(f"Applying bonus for effect {effect}: {i_bonuses[effect]}")
                    item.value *= i_bonuses[effect]
                    i_bonuses.pop(effect, None)  # Remove the bonus after applying it to avoid double application


        #Add conditional effects based on the item's current effects (1 per effect)
        for effect, addition in self.cond_effect_add.items():
            for _ in range(item.effects.count(effect)):
                if super_verbose:
                    print(f"Adding conditional effect {addition} to item because it has effect {effect}.")
                item.effects.extend([addition])
                if addition in i_bonuses:
                    if super_verbose:
                        print(f"Applying bonus for conditional effect {addition}: {i_bonuses[addition]}")
                    item.value *= i_bonuses[addition]
                    i_bonuses.pop(addition, None)  # Remove the bonus after applying it to avoid double application

        #Transform effects based on trans_effect mapping (1 per effect)
        for index, effect in enumerate(item.effects):
            if effect in self.trans_effect:
                item.effects[index] = self.trans_effect[effect]
                if super_verbose:
                    print(f"Transforming effect {effect} to {self.trans_effect[effect]} on item.")
                if self.trans_effect[effect] in i_bonuses:
                    if super_verbose:
                        print(f"Applying bonus for transformed effect {self.trans_effect[effect]}: {i_bonuses[self.trans_effect[effect]]}")
                    item.value *= i_bonuses[self.trans_effect[effect]]
                    i_bonuses.pop(self.trans_effect[effect], None)  # Remove the bonus after applying it to avoid double application

        #Multiply the item's value by (1 - destroy_chance) to simulate the chance of destruction
        if self.destroy_chance > 0:
            if super_verbose:
                print(f"Applying destroy chance of {self.destroy_chance} to item.")
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

    def process(self, item, verbose=False, super_verbose=False):

        #If the processor has onlyaccept effects and the item does not have any of those effects, set the item's value to 0
        if self.onlyaccept and not any(effect in item.effects for effect in self.onlyaccept):
            item.value = 0
            if verbose:
                print(f"Processor {self.name} refused item because it did not have {self.onlyaccept}.")

        #If the processor has refuse effects and the item has any of those effects, set the item's value to 0
        if any(effect in item.effects for effect in self.refuse):
            item.value = 0
            if verbose:
                print(f"Processor {self.name} refused item because it was {effect}.")

        #Multiply the item's value by the processor's multiplier and apply rarity multiplier
        item.value *= self.mult
        item.value = apply_rarities(self.rarity, item.value)

        #Apply bonuses to the item's value if the item has the corresponding effect
        for effect in self.bonus:
            if effect in item.effects:
                if super_verbose:
                    print(f"Applying bonus for effect {effect}: {self.bonus[effect]}")
                item.value *= self.bonus[effect]
        return item