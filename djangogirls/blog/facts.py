import random

CS_TIDBITS = [
    "The first computer bug was an actual moth, found in a Harvard Mark II relay in 1947.",
    "COBOL, written in 1959, still runs in the core banking systems of many major banks today.",
    "The QWERTY keyboard layout was designed to slow typists down and reduce typewriter jams.",
    "'Debugging' predates computers — Thomas Edison used the term for tracking down issues in 1878.",
    "The first 1GB hard drive (1980) weighed about 550 pounds and cost $40,000.",
    "Python was named after Monty Python's Flying Circus, not the snake.",
    "More than 90% of the world's currency exists only as digits in computer databases.",
    "The '@' symbol was chosen for email in 1971 because it was rarely used and unlikely to cause confusion.",
    "A single Google search uses about the same amount of energy as boiling a small amount of water for tea.",
    "The term 'algorithm' comes from the name of 9th-century mathematician Al-Khwarizmi.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
    "Why do Java developers wear glasses? Because they don't C#.",
    "There are only 10 types of people: those who understand binary and those who don't.",
    "Why did the programmer quit their job? Because they didn't get arrays.",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
    "I told my computer I needed a break, and now it won't stop sending me KitKats.",
    "Why was the function sad after leaving its parent? It didn't get called back.",
    "A byte walks into a bar looking miserable. The bartender asks what's wrong. It says, 'Parity error.'",
    "Why do programmers hate nature? It has too many bugs and no debugger.",
]


def get_random_tidbit():
    return random.choice(CS_TIDBITS)
