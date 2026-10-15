"""Play every loop listed in Delahaye and Mathieu's records file (records_C4_naturelle.py, rangement naturel) and walk
one lap of its cycle: lap length, pairs turned over, battles (tricks whose first pair ties), and whether the loop is
aligned (from some position with equal hands, both players turn over exactly their n/2 cards by the end of a trick,
the hands are equal again, and so on around the lap). Uses war_engine.py, not their program."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from war_engine import play_to_cycle, aligned, trick

LOOPS = {   # the deals as their records file lists them, player 1 then player 2, top card first
    'V3 (19)': ([3, 2, 1, 1, 2, 1], [2, 1, 3, 2, 3, 3]),
    'V4 #1': ([4, 2, 4, 1, 3, 1, 3, 3], [2, 1, 4, 4, 3, 2, 2, 1]),
    'V4 #2': ([3, 1, 3, 3, 2, 1, 4, 4], [3, 2, 2, 1, 4, 2, 4, 1]),
    'V4 #3': ([3, 1, 3, 3, 4, 1, 4, 4], [3, 2, 2, 1, 4, 2, 2, 1]),
    'V4 #4': ([2, 1, 4, 4, 2, 1, 3, 3], [4, 2, 4, 1, 3, 2, 3, 1]),
    'V6 (36)': ([4, 2, 5, 5, 4, 2, 6, 6, 3, 2, 2, 1], [5, 4, 5, 1, 6, 4, 6, 1, 3, 1, 3, 3]),
    'V8 (48)': ([8, 5, 5, 1, 6, 2, 6, 6, 7, 2, 7, 7, 4, 2, 4, 4], [8, 1, 8, 8, 6, 5, 5, 1, 7, 3, 3, 1, 4, 3, 3, 2]),
    'V11 Courbet': ([1, 3, 4, 9, 4, 9, 6, 5, 10, 7, 6, 10, 5, 7, 10, 11, 11, 2, 8, 7, 9, 5],
                    [8, 1, 4, 1, 4, 8, 2, 11, 6, 3, 7, 2, 8, 3, 9, 1, 2, 3, 10, 5, 6, 11]),
}

for name, (p1, p2) in LOOPS.items():
    cyc = play_to_cycle(p1, p2)
    if cyc is None:
        print('%-12s ENDS' % name); continue
    lam = len(cyc); al, bat = aligned(cyc[0], lam)
    a, b = list(cyc[0][0]), list(cyc[0][1]); flips = 0
    for _ in range(lam): flips += trick(a, b)
    print('%-12s %2d cards: lap %5d tricks, %5d pairs turned, %4d battles, %s'
          % (name, len(p1) + len(p2), lam, flips, bat, 'ALIGNED, phase %d tricks' % al if al else 'not aligned'))
