"""Checks played with war_engine.py (rangement naturel, real battles):
1. stacking aligned loops: disjoint values, overlapping values, same values;
2. every 4|4 deal of the four 8-card atom patterns, and whether its cycle is aligned;
3. the two 12-card aligned loops that exist when one value may have 5 copies.
usage: python stack_checks.py"""
import os, sys
from collections import Counter
from itertools import permutations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from war_engine import play_to_cycle, aligned

sh = lambda h, d: [c + d for c in h]
X1, X2 = [2, 1, 4, 4, 3, 2, 3, 1], [4, 2, 4, 1, 2, 1, 3, 3]                       # a 16-card aligned loop, at a phase start
B1, B2 = [2, 1, 4, 4, 3, 1, 3, 3], [4, 2, 4, 1, 3, 2, 2, 1]                       # another 16-card aligned loop
Y1, Y2 = [4, 2, 6, 6, 4, 1, 5, 5, 3, 1, 3, 3], [6, 4, 6, 2, 5, 4, 5, 1, 3, 2, 2, 1]  # a 24-card aligned loop
print('1. stacking')
for name, (p1, p2) in {'16 then 24 cards (values 1-4, 5-10)': (X1 + sh(Y1, 4), X2 + sh(Y2, 4)),
                       '24 then 16 cards': (sh(Y1, 4) + X1, sh(Y2, 4) + X2),
                       '24 low, 16 high': (Y1 + sh(X1, 6), Y2 + sh(X2, 6)),
                       '16 on itself (same values)': (X1 + X1, X2 + X2),
                       '16 on another 16 (same values)': (X1 + B1, X2 + B2),
                       '(2,2,4) atom on {1,2,3} + on {1,2,4}': ([3, 2, 3, 1, 4, 2, 4, 1], [2, 1, 3, 3, 2, 1, 4, 4])}.items():
    c = play_to_cycle(p1, p2)
    print('   %-40s %s' % (name, 'cycle of %d tricks' % len(c) if c else 'ENDS'))

print('2. every 4|4 deal of the 8-card atom patterns')
for pat in [(2, 2, 4), (1, 1, 2, 4), (2, 1, 1, 4), (1, 1, 1, 1, 4)]:
    deck = [v + 1 for v, m in enumerate(pat) for _ in range(m)]
    deals = sorted(set(permutations(deck))); kinds = Counter()
    for d in deals:
        c = play_to_cycle(d[:4], d[4:])
        if c:
            al, bat = aligned(c[0], len(c))
            kinds['lap %d, %s' % (len(c), 'aligned' if al else 'NOT aligned')] += 1
    print('   %-14s %4d ordered deals, cycling: %s' % (pat, len(deals), dict(kinds)))

print('3. 12-card aligned loops with a 5-copy value (no 4-copy limit)')
for p1, p2 in [([2, 1, 3, 2, 3, 1], [4, 3, 3, 2, 2, 2]), ([2, 1, 3, 3, 1, 1], [3, 1, 2, 2, 3, 3])]:
    c = play_to_cycle(p1, p2); al, bat = aligned(c[0], len(c))
    print('   %s | %s  counts %s: cycle of %d tricks, %d battles, %s' % (p1, p2, dict(sorted(Counter(p1 + p2).items())), len(c), bat,
                                                                 'ALIGNED, phase %d tricks' % al if al else 'not aligned'))
