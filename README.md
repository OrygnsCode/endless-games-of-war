# Endless games of War

Programs and data for counting the deals of the card game War that never end, for decks of
up to 16 cards. They back the paper *Endless Games of War: Counting the Deals That Never End*
(Daniel Okwor, 2026).

## The game

There are n cards, numbered 1 to n, and two players. The deck is dealt alternately with
the first card to player 1, so player 1 holds ceil(n/2) cards and player 2 floor(n/2). On
each turn both players turn over their top card. The higher card wins, and the winner puts
the winning card and then the losing card under their own pile. A player with no cards
loses. With one card of each rank there are no ties. This is the version of War studied by
Spivey (2010).

Nobody makes a decision once the cards are dealt, so every deal either ends or reaches a
position it has seen before and repeats forever. a(n) is the number of the n! deals whose
game never ends.

## Result

| n | a(n) | share of all n! deals | longest game that ends (turns) |
|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 |
| 2 | 0 | 0 | 1 |
| 3 | 0 | 0 | 3 |
| 4 | 0 | 0 | 6 |
| 5 | 30 | 0.2500 | 8 |
| 6 | 0 | 0 | 15 |
| 7 | 2,304 | 0.4571 | 15 |
| 8 | 0 | 0 | 26 |
| 9 | 218,680 | 0.6026 | 28 |
| 10 | 395,940 | 0.1091 | 49 |
| 11 | 28,223,770 | 0.7071 | 41 |
| 12 | 0 | 0 | 74 |
| 13 | 4,880,546,113 | 0.7838 | 57 |
| 14 | 3,790,165,176 | 0.0435 | 461 |
| 15 | 1,095,264,882,758 | 0.8376 | 80 |
| 16 | 0 | 0 | not computed |

Each value was computed by at least two programs that share no code (see Programs below).
Spivey published a(10) = 395,940, and Delahaye and Mathieu (2025) searched the deals for
n = 2, 3, 4, 6, 8 and 12 and found no cycle; all of these agree.

The zeros fall at n = 1, 2, 3, 4, 6, 8, 12, 16, the numbers of the form 2^k or 3 * 2^k.
Spivey showed that every other n has deals that never end, and asked whether, for these n,
any position at all cycles. For n up to 16 none does, whether or not a deal can produce it.
Card n never loses, so it never changes hands, and in a game that never ends it keeps coming
back to the top of its holder's pile. Up to exchanging the players, every cycle therefore
passes through a position in which player 1's top card is n. We call these the canonical
positions; there are (n-1)! * (n-1) of them, and it is enough to play them all. For n = 16
that is 19,615,115,520,000 positions, and none of them cycles.

## The cycles themselves

For odd n every cycle has a rigid shape: the players take turns winning, and each pile
alternates between cards that never lose and cards that always lose. A position on a cycle
is then a way of filling fixed slots with the cards, subject only to which cards ever meet,
so the positions on cycles are counted by the linear extensions of a small partial order,
one for each split of the cards between the players. `counting/odd_formula.py` turns this
into the exact number of cycles without playing any game:

| n | 5 | 7 | 9 | 11 | 13 | 15 | 17 | 19 |
|---|---|---|---|---|---|---|---|---|
| cycles | 2 | 52 | 336 | 55,592 | 319,680 | 48,304,896 | 3,588,302,592 | 653,644,195,200 |

A cycle and the same cycle with the players exchanged count as one. For n <= 13 these values
agree with a scan of every canonical position (`gpu/war_gpu.py --canon --distinct` and
`cpu/distinct_cycles.c`), and for every odd n <= 15 with `cpu/odd_cycles.c`, which plays every
position of the shape the cycles must have. For n = 17, `python odd_formula.py 17 17 --split` gives
1,828,915,200 canonical positions on cycles in which player 1 holds 8 cards and 3,249,590,400
in which player 1 holds 10, and `cpu/odd_cycles.c` finds the same numbers. The paper also
gives a closed form when (n+1)/2 is prime.

The same method counts, for every n, the cycles of the kind Spivey constructs (his
Theorem-3 type), including even n (`counting/t3_count.py`). The paper proves that every such
cycle has a length divisible by n + 2^v, where 2^v is the largest power of 2 dividing n, by
following single cards through the cycle; `counting/t3_period.py` compares that description
of the cycle lengths with the forced play of the slot pattern in `counting/t3_count.py` for
every n = m * 2^v <= 64 with m odd, m >= 5 and 2^v <= 8. The tables in `data/` give the
number of cycles, split by length, for odd n <= 41 (for odd n all cycles are of Spivey's
kind), and the number of cycles of Spivey's kind for even n <= 46.

Spivey also asked whether cycles of any other kind exist (his Question 1). The smallest deck
with one has 14 cards: of the 26,640 cycles of 14 cards, 720 are not of Spivey's kind, all of
length 96, and 61,184,620 of the 3,790,165,176 endless deals end in one of them. The paper
constructs such cycles for every n = m * 2^v with m = 3 (mod 4), m >= 7 and v >= 1, and
shows that ordinary deals reach them. The scripts in `families/` write these n as
n = 2^(j+1) (4k+3), so j = v - 1 counts the doublings of the family n = 8k+6. They check the
construction at the level of card categories for j <= 6, and the deals that reach it with
numbered cards for up to 1,472 cards. Two more families live at n = 8N + 6, one of them with
2N + 3 categories, so these cycles can have arbitrarily many categories (every odd number from 5 on); `families/more_families.py`
checks both and places the six kinds of such cycles that random sampling finds at n = 22.

## Programs

Four programs that share no code count the deals:

| program | platform | cycle test | pile layout | used for |
|---|---|---|---|---|
| `gpu/war_gpu.py` | GPU | Brent | 4-bit cards, top card in the low bits | deals n <= 15; canonical positions n <= 14 and n = 16 |
| `gpu/war_gpu_floyd.py` | GPU | Floyd | 4-bit cards, top card in the high bits | deals 2 <= n <= 15; canonical positions 2 <= n <= 14 and n = 16 |
| `cpu/war.cpp` | CPU | Brent | 4-bit cards, top card in the low bits | deals 2 <= n <= 15 |
| `cpu/war_floyd.c` | CPU | Floyd | circular byte buffers | deals 2 <= n <= 14; every position for n = 9 and 12 |

All four agree for 2 <= n <= 14, the two GPU programs and `cpu/war.cpp` for n = 15, and the
two GPU programs on the 16-card position scan. `gpu/war24.py`, a third GPU program with 5-bit
cards, also gives a(14). `cpu/war_all.cpp` plays every position (every order and every split)
and, with `cpu/war_floyd.c`, confirms that no 12-card position cycles. The plain simulators
`reference/war_ref.py` and `reference/oeis_program.py` reproduce the small terms directly
from the rule. `gpu/war17.py` and `gpu/war24.py` go past 16 cards.

The other programs look at the cycles themselves:

- `cpu/distinct_cycles.c` counts the cycles, by a different method from
  `gpu/war_gpu.py --canon --distinct`;
- `cpu/odd_cycles.c` counts them for odd n from the shape the cycles must have;
- `cpu/reach_cycles.c` checks for n <= 14 that every cycle, or the same cycle with the
  players exchanged, is entered by an ordinary deal;
- `cpu/sampler.c` plays random positions for larger n;
- `cpu/base_search.c` searches small letter positions whose doubling is a cycle not of
  Spivey's kind, and `cpu/base_enum.c` repeats the search, written independently, also with
  five or six letters; `families/classify_doubled.py` sorts the cycles it finds by length and
  category sizes;
- `cpu/cycle_length.c` finds the cycle that the game from one given position ends in, and
  how many turns it takes to get there.

`cpu/loser_first.c` counts the deals that never end when the losing card goes under the
winner's pile first, as do `gpu/war_gpu.py --rule 1`, `gpu/war_gpu_floyd.py --loser-first`
and `cpu/war.cpp` with mode 1 (`data/loser_first.tsv`). With this rule no position of 16 cards
cycles either: both GPU programs scanned every canonical position (`data/long_runs.txt`).

Several checks are written two or three times, in different ways, so that a mistake in one
shows up as a disagreement: `cpu/base_search.c` and `base_enum.c` (the search over letter
positions); `families/doubled_phases.py`, `doubled_check.py` and
`doubled_family.py` (the doubled family at the letter level); `families/reach_family.py` and
`reach_check.py` (the deals that reach it); `families/family_construct.py` and
`family_check.py` (the family n = 8k+6); `cycles/inspect_loops.py` and `loop_shape.py`
(the winners around a loop). `counting/slot_check.py` is a stricter form of the self-check in
`counting/odd_count.py`: it plays every way of filling the slots until the game ends or
repeats, not only for one cycle length.

## Layout

```
gpu/         the GPU programs (Python with CuPy)
cpu/         the C and C++ programs (OpenMP)
reference/   plain Python simulators, straight from the rule
counting/    the cycle counts for odd n and for Spivey's kind, and their checks
families/    the cycles that are not of Spivey's kind: construction and checks
cycles/      tools for single cycles: categories, cycle lengths, the canonical-position check
figures/     the scripts for the figures in the paper
data/        the results (see data/README.md)
```

## Reproduce

The GPU programs need Python 3, CuPy and an NVIDIA GPU; the runs here used an NVIDIA RTX
5080 with 16 GB. The C and C++ programs need a compiler with OpenMP; each file gives its
build line, for example `gcc -O3 -march=native -fopenmp -o distinct_cycles distinct_cycles.c`
and `g++ -O3 -march=native -fopenmp -o war war.cpp`. Everything else needs only Python 3.9 or
later. The commands below start in the repository root.

Without a GPU, the program from the OEIS entry prints a(1) to a(10) in about half a minute:

```
python reference/oeis_program.py
```

Every term up to a(13), with the cycle lengths, in under a minute:

```
cd gpu
python war_gpu.py 13 --nmin 1 --hist 256
```

a(14) takes a few minutes, a(15) a little over an hour, and the scan of every 16-card
canonical position about four hours. Long runs write their progress to `<out>.progress` and
continue from it with `--resume`:

```
cd gpu
python war_gpu.py 14 --half --hist 256
python war_gpu.py 15 --hist 256 --out n15 --resume
python war_gpu.py 16 --canon --shape --out n16c --resume
```

a(13) from the second GPU program and from the two CPU programs (each takes one n):

```
cd gpu
python war_gpu_floyd.py 13
cd ../cpu
./war 13 0
./war_floyd 13 0
```

The number of cycles, by formula and by search:

```
cd counting
python odd_formula.py 21
python t3_count.py 10 14 18 20 22
python tables.py      # rewrites the two tables in data/, about 45 minutes
cd ../gpu
python war_gpu.py 13 --nmin 5 --canon --distinct --shape
cd ../cpu
./distinct_cycles 13 8
```

## Checks

`gpu/war_gpu.py` and `gpu/war17.py` stop with an error unless the number of deals (or
positions) they played is exactly n! (or (n-1)! * (n-1)); `gpu/war_gpu_floyd.py` and
`gpu/war24.py` print both numbers and exit with an error if they differ; the CPU deal counters
(`war.cpp`, `war_floyd.c`, `war_all.cpp`, `loser_first.c`) print the total next to the
result. In every run in `data/` the number played is the full count. `cycles/canon_check.py`
compares the scan of the canonical positions with a scan of every position for n <= 9. The
test that decides whether a cycle is of Spivey's kind has a negative control in
`gpu/war_gpu_floyd.py`: given the wrong block length with `--q1 --block`, it rejects every cycle.
The output of these checks, and of the long runs, is in `data/long_runs.txt` and
`data/checks.txt`.

## References

- M. Z. Spivey, Cycles in War, *Integers* 10 (2010), #G02, 747-764.
- J.-P. Delahaye and P. Mathieu, Jeu de la bataille : à la recherche des parties infinies,
  *Pour la Science* 567 (January 2025), 80-85. Code: https://github.com/cristal-smac/bataille

## Author

Daniel Okwor, Orygn LLC, Houston TX. Contact: daniel@orygn.tech.

## License

MIT. See LICENSE.
