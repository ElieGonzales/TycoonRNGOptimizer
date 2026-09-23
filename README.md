# Tycoon RNG : Refinery Optimizer

TRRO is a tool developed to help you optimize your setup to maximize profit in the game Tycoon RNG: Refinery.
It uses an asynchronous Genetic Algorithm to find the best value without much computing power and without having to check all 60 quadrillion combinations.

## Features

- Random runs to avoid shallow bests
- A comprehensive and easy way to pass in available buildings
- An estimated value
- Handling of complex tag interactions, rarity multipliers, and more through an in-depth class system
- Future-proof with clear syntax and buildings interactions. Adding a building is done with a single line!

## Installation and use

This is now available at a website! You can find it here:
<https://eliegonzales.github.io/TycoonRNGOptimizer/>

You can install this project as a PyPi package:
 ```python3 -m pip install rngoptimizer```

Open your terminal in a directory with a text file containing your buildings as directed below.
You can then pass in the flags `-p <path>` for the path to your text file if it isn't `available_buildings.txt`, `-d` for the dropper amount, `-u` for the upgrader amount and `-r` for the number of runs.

1. Download the source code by clicking the green **Code** button on the top right and **Download ZIP**.
2. Unzip the file.
3. Write your available buildings in `available_buildings.txt` or another text file in the same directory using the following syntax:

   **RARITY1 RARITY2 RARITY3 - BUILDING NAME**

   For example:
   - **Negative Overpowered - slime duper** is correct
   - **oP h - AnCieNt rUins** is correct
   - **hyperspace Electric Dropper** is incorrect
   - **n - magicaltree** is incorrect

   Comments can be written if the line starts with #.
   You can set a custom default dropper and upgrader count by typing @Dropper amount: x and @Upgrader amount: y at the start of the file.
4. run `runme.py`. Make sure you have python installed.
5. When prompted, enter the number of droppers slots you have on your base, the number of upgraders, and the preset. To use the default value, press enter. *(Default value can also be set in `available_buildings.txt`)*
6. Wait for the program to finish.
7. The last line will be the best found buildings and the estimated value produced. It will also be saved to `optimized_buildings.txt`.
8. Done!

## Frequently Asked Questions

### Is this safe?

Yes. It does not read from any file other than available_buildings.txt and does not write to any file other than optimized_buildings.txt. This is a fully open-source project, and anyone with Python experience can confirm this program does what it says it does.

### Is this linked to my Roblox Account?

No. It requires you to manually add in your own buildings by writing them down. It does not have access to your Roblox account, and requires no login.

### I can't open runme.py

Make sure you have Python 3.14 installed. you can find it here: [Python Download](https://www.python.org/downloads/)

### `<Building>` isn't recognized

The building might've been added in a recent update. You can notify me on the TR:R Discord or DM me: **@Elie07**

### The factory found is worse than the one I have right now

The algorithm isn't perfect, and is by definition not very intelligent. It's basically a better trial-and-error. I'm working on upgrading the algorithm to be more performant.

### I built the recommended factory, but it doesn't perform the same

I'm not affiliated with the TR:R developement team and have no way to check if my calculations are accurate. If you run into this issue, please send me your available buildings, the setup the algorithm gave you and what you're getting in game via discord: **@Elie07**
