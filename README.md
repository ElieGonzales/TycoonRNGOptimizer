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
1. Download the source code by clicking the green **Code** button on the top right and **Download ZIP**.
2. Unzip the file.
3. Write your available buildings in available_buildings.txt or another text file in the same directory using the following syntax:

   **RARITY1 RARITY2 RARITY3 - BUILDING NAME**

   Capitalization is important. For example:
   - **Negative Overpowered - Slime Duper** is correct
   - **OP H - Ancient Ruins** is correct
   - **Hyperspace Electric Dropper** is incorrect
   - **negative magical tree** is incorrect
4. run *runme.py*. Make sure you have python installed.
5. When prompted, enter the number of droppers slots you have on your base, the number of upgraders, and the preset. To use the default value, press enter. *(Default value can also be set in available buildings.txt)*
6. Wait for the program to finish.
7. The last line will be the best found buildings and the estimated value produced. It will also be saved to *optimized_buildings.txt*.
8. Done!

## Frequently Asked Questions

<details>
<summary><b>Is this safe?</b></summary>
<br>

Yes. It does not read from any file other than available_buildings.txt and does not write to any file other than optimized_buildings.txt. This is a fully open-source project, and anyone with Python experience can confirm this program does what it says it does.

</details>


<details>
<summary><b>Is this linked to my Roblox Account?</b></summary>
<br>

No. It requires you to manually add in your own buildings by writing them down. It does not have access to your Roblox account, and requires no login.

</details>


<details>
<summary><b>I can't open runme.py!</b></summary>
<br>

Make sure you have Python 3.14 installed. you can find it [here.](https://www.python.org/downloads/)

</details>

<details>
<summary><b>&lt;Building&gt; isn't recognized!</b></summary>
<br>

The building might've been added in a recent update. You can notify me on the TR:R Discord or DM me: **@Elie07**

</details>

<details>
<summary><b>The factory found is worse than the one I have right now!</b></summary>
<br>

The algorithm isn't perfect, and is by definition not very intelligent. It's basically a better trial-and-error. I'm working on upgrading the algorithm to be more performant. 

</details>

<details>
<summary><b>I built the recommended factory, but it doesn't perform the same!</b></summary>
<br>

I'm not affiliated with the TR:R developement team and have no way to check if my calculations are accurate. If you run into this issue, please send me your available buildings, the setup the algorithm gave you and what you're getting in game via discord: **@Elie07**

</details>