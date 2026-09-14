# Tycoon RNG : Refinery Optimizer 
TRRO is a tool developed to help you optimize your setup to maximize profit in the game Tycoon RNG: Refinery.
It uses an asynchronous Genetic Algorithm to find the best value without much computing power and without having to check all 60 quadrillion combinations.
## Features
- A preset mode to adapt the genetic algorithm to your specific build
- A comprehensive and easy way to pass in available buildings
- An estimated value
- Handling of complex tag interactions, rarity multipliers, and more through an in-depth class system

## Installation and use
1. Download the source code by clicking the green **Code** button on the top right and **Download ZIP**.
2. Unzip the file.
3. Write your available buildings in available_buildings.txt or another text file in the same repository using the following syntax:

   **RARITY1 RARITY2 RARITY3 - BUILDING NAME**

   Capitalization is important. For example:
   - **Negative Overpowered - Slime Duper** is correct
   - **negative magical tree** will not work
4. run *runme.py*. Make sure you have python installed.
5. When prompted, enter the number of droppers slots you have on your base, the number of upgraders, and the preset. To use the default value, press enter.
6. Wait for the program to finish.
7. The last line will be the best found buildings and the estimated value produced. It will also be saved to *optimized_buildings.txt*.
8. Done!
