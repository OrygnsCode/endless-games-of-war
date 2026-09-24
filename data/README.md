# Data

The `.tsv` files are tab-separated, with a header line starting with `#`. `b_file.txt` is in the
OEIS b-file format (one `n a(n)` pair per line). "Cycles" are counted once per pair {cycle, same
cycle with the players exchanged}.

| file | contents |
|---|---|
| `b_file.txt` | a(n) for n = 1..16 |
| `deals.tsv` | for each n: the number of deals, how many never end, the longest game that ends (in turns), and the endless deals split by the length of the cycle they end in |
| `canonical_positions.tsv` | for each n: the (n-1)! (n-1) positions in which player 1's top card is n, how many of them lead into a cycle, how many lie on one, and the number of cycles |
| `odd_n_cycles.tsv` | odd n up to 41: the number of cycles from the formula for odd n, the split by length, and the canonical positions on a cycle |
| `spivey_type_cycles.tsv` | even n up to 46: the number of cycles of Spivey's Theorem-3 type, with the split by length (for odd n every cycle is of that type, so `odd_n_cycles.tsv` has them) |
| `loser_first.tsv` | the same count when the losing card goes under the winner's pile first, n = 2..15 |
| `long_runs.txt` | the final output lines of the runs for n = 13 to 16, and of two sample runs at n = 17, as the programs printed them |
| `doubled_bases.txt` | every letter position (m = 7 and 11 cards, four to six different letters, every word and every split) whose doubling is a cycle not of Spivey's Theorem-3 type, as `cpu/base_enum.c` lists them; `families/classify_doubled.py` reads it |
| `sampler_n22_list.txt` | the output of `cpu/sampler 22 10000000 8 22 pos 20000000 list`: for each of the 318 sampled 22-card positions that reach a cycle not of Theorem-3 type, its sample number and a position on that cycle; `families/more_families.py` reads it |
| `checks.txt` | the output of the shorter runs and checks: the deal counters at small n, the negative controls, the counts of distinct cycles, the families |

In the output of `gpu/war_gpu_floyd.py`, `q1_nonTheorem3_loops` is the number of cycling positions
whose cycle is not of Spivey's Theorem-3 type (the subject of his Question 1). With `--half` it counts
only the half of the deals that was played, like `cycling_found`: for n = 14, 30,592,310 x 2 = 61,184,620.

## Where the numbers come from

`deals.tsv` for n <= 13 and the loser-first values for n <= 13 are reproduced in about a minute:

```
cd gpu
python war_gpu.py 13 --nmin 1 --hist 256
python war_gpu.py 13 --nmin 2 --rule 1
```

The rows for n = 14 and 15 come from the long runs in `long_runs.txt`: `gpu/war_gpu.py --half` for
n = 14 (a few minutes) and `gpu/war_gpu.py` for n = 15 (a little over an hour), each confirmed by
`gpu/war_gpu_floyd.py` and `cpu/war.cpp`. a(16) = 0 follows from the scan of all 16-card canonical
positions, which found no cycle (both GPU programs). The longest ending game for n = 16 needs every
16-card deal and has not been computed.

`canonical_positions.tsv` for n <= 14 comes from `gpu/war_gpu.py N --canon --distinct` (`checks.txt`,
and `long_runs.txt` for n = 14), and for 5 <= n <= 14 it agrees with `cpu/distinct_cycles.c`
(`checks.txt`). For n = 15 the positions on
a cycle and the number of cycles come from the formula for odd n and from `cpu/odd_cycles.c`, which
agree; the number of positions that lead into a cycle was not computed.

`odd_n_cycles.tsv` and `spivey_type_cycles.tsv` are written by `counting/tables.py`. With the default
limits it ran for about 45 minutes here on one core, most of it for the largest n.

The loser-first values up to n = 13 were computed by `gpu/war_gpu.py --rule 1`,
`gpu/war_gpu_floyd.py --loser-first` and `cpu/loser_first.c`, n = 14 by those three and
`cpu/war.cpp` (mode 1), and n = 15 by the two GPU programs. With this rule both GPU programs also
scanned every canonical position for n = 2..12 (`checks.txt`) and n = 16 (`long_runs.txt`): no
position of 2, 4, 8 or 16 cards cycles, so the loser-first count is 0 for n = 16 as well.
