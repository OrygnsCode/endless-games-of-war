# Decks with suits

Programs and data for the section *Decks with suits* of the paper: War with several cards of each
value, where equal cards start a battle. They answer, for small decks, whether a deal can go on
forever, and they test the one known way of building such deals for many values.

## The rules

The rules are those of the program `bataille.py` of Delahaye and Mathieu
([cristal-smac/bataille](https://github.com/cristal-smac/bataille)), with the winner's card
first ("rangement naturel"). Each player turns over the top card. If the cards differ, the higher
one wins the trick. If they are equal, both stay on the table and the players turn over their
next cards, with no card face down, until one card wins. The table goes to the winner, last
pair first and the winning card first within it. If a hand runs out during a battle, the cards on
the table go to nobody and the game ends; if both hands are empty it is a draw. A deal gives the
first half of the shuffled deck to player 1. Games are counted up to exchanging the players, as
Delahaye and Mathieu count them.

## Programs

| file | what it does |
|---|---|
| `battles.cpp` | plays every deal (or random deals) of V values in C suits and finds the deals that never end, Brent's method on the positions at the start of each trick; the longest games; the aligned loops |
| `shapes.cpp` | finds the aligned loops on every multiset of N cards at once, from the shapes of the phases (which columns tie, who wins each trick); exact |
| `run_parts.py` | runs `shapes` in parts side by side, each resuming from its own file |
| `shape_orbits.py` | a second shape search, in Python, written independently of `shapes.cpp`: builds whole phase shapes, prunes after every phase, and checks the return condition with union-find |
| `atoms.py` | the phase map in plain Python: the aligned loops of Delahaye and Mathieu split into 8-card atoms, the structure of that atom and its merged forms, and a 12-card aligned loop with 5 copies of a value |
| `theorem3/t3_suits.py` | for each shape of a cycle of Theorem-3 type: the level sizes, whether every card of a level meets every card of the next one, and whether the cards can be given ranks with 2 or 4 suits so that no two equal ranks meet (SAT, needs `python-sat`) |
| `theorem3/t3_routes.py` | the number of meetings between adjacent levels, predicted from the routes the cards travel and compared with a full cycle, for every shape up to a given size |
| `theorem3/spivey52.py` | Spivey's 52-card cycle: its length, the sizes of its categories, and which categories meet |
| `theorem3/courbet44.py` | Courbet's 44-card loop under the rules above: where it enters its cycle, the length of the cycle, no tie on it, runs of 4 wins, categories and shape |
| `make_results.py` | writes `RESULTS.txt`: the command and output of every search here (it runs `make_results_C.py` for the `theorem3/` and `atoms.py` part) |
| `checks/` | a second, short engine in Python (`war_engine.py`) that replays the loops of Delahaye and Mathieu's records file, the stacks and every deal of the 8-card atoms; `dm_crosscheck.txt` is the output of the same checks with the cycle search done by their own `bataille.py` (identical; their program is GPL-3.0 and is not included) |
| `battle_free/` | the meetings of the cards in Spivey's 52-card cycle and in the cycles of Theorem-3 type, and an exact search for a numbering of their slots with 4 cards of each value and no tie; uses `../counting/t3_count.py`. `theorem3/` is written independently of it and checks the same facts another way |

A loop is *aligned* when, from some position where both players hold n/2 cards, each player turns
over exactly those cards by the end of a trick and again holds n/2 cards, phase after phase. Aligned
loops can be stacked into one larger loop, since cards of the two blocks never meet. The *phase map*
takes such a position to the next one, and the aligned loops are its periodic points, so every
deal can be tested with a few dozen flips.

## Results

| deck | games (up to exchanging the players) | never end | longest game with a winner |
|---|---:|---:|---|
| 2 values x 4 suits | 38 | 0 | 4 tricks, 8 cards turned |
| 3 values x 4 suits | 17,370 | 360 (one cycle of 19 tricks) | 37 tricks, 54 cards |
| 4 values x 4 suits | 31,532,760 | 8,545 (four aligned cycles of 24 tricks) | 142 tricks, 192 cards |
| 5 values x 4 suits | 152,770,174,200 | 0 | 453 tricks, 562 cards |

The first three rows agree with the counts Delahaye and Mathieu list; the longest 20-card game is
the one in their records file. With 5 values every one of the 305,540,235,000 deals ends, in a win
or in a draw (16,364,944 deals).

Aligned loops, for every multiset with at most 4 cards of a value:

* 4, 6, 10 and 12 cards: none (every deal tested).
* 8 cards: one loop up to merging values that never meet, on the counts (1,1,1,1,4), (1,1,2,4),
  (2,1,1,4) and (2,2,4); the aligned loops of Delahaye and Mathieu with 16, 24 and 32 cards are
  stacks of it.
* 16 cards, phase period at most 5: only the stacks of two 8-card loops.
* 20 cards, phase period at most 5: none.

With 5 or more copies of a value there are aligned loops of 12 and of 20 cards, so the limit of 4
copies matters for what holds at 52 cards.

Cycles of Theorem-3 type with suits. In every cycle of Theorem-3 type with 52 cards (all five shapes),
each card of a category meets each card of the next one, so the four cards of a rank would all have
to sit in one category; the category sizes are 6, 19, 20 and 7, so no such cycle can be played with
4 suits (or 2) without a battle. For n = 4m this happens for every shape exactly when (m+1)/2 and
(3m-1)/2 are both prime. With 11 values in 4 suits (44 cards) every shape can be played without a
battle, and Courbet's 44-card loop is one of these, of shape (2, 3). The route prediction matches a
full cycle for every shape with n = m * 2^v up to 124 and v at most 3.

## Running

```
g++ -O3 -mtune=native -fopenmp -o battles battles.cpp
g++ -O3 -mtune=native -o shapes shapes.cpp
./battles 4 4 0 8 1                      # every deal of 4 values in 4 suits, 8 threads, each game once up to exchanging the players
./battles M 10 8                         # aligned loops on every multiset of 10 cards
./shapes 16 4                            # aligned loops of 16 cards, phase period dividing 4
python make_results.py                   # every search, into RESULTS.txt
```

The Python scripts need only the standard library, except `theorem3/t3_suits.py`, which needs
`python-sat` (`pip install python-sat`) for its SAT step.

On Windows build without `-march=native`: MinGW-w64 does not align the stack for AVX code, and
such a build can crash. The long searches write one line per finished chunk to a file in `data/`
and skip finished chunks when started again; `make_results.py` reads those files.

| file in `data/` | contents |
|---|---|
| `v5_aligned.chunks` | `./battles A 5 4 0 4 6`: every deal of 5 values in 4 suits through the phase map |
| `v5_full.chunks` | `./battles F 5 4 0 4 6`: every deal of 5 values in 4 suits played to its end |
| `atoms12.patterns` | `./battles M 12 4`: every multiset of 12 cards |
| `shapes20_period4_*.txt`, `shapes20_period5_*.txt` | `python run_parts.py ./shapes 20 k 0 4 8 data/shapes20_periodk`, k = 4, 5 |
