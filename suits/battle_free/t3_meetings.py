"""For every Theorem-3 shape (a, b) of the given deck sizes: Spivey's categories of the slots, their sizes, and how
many pairs of adjacent categories meet over one full cycle (each card keeps the identity of its starting slot).
When adjacent categories meet completely, a numbering with 4 cards of each value and no tie must give whole
values to whole categories, which is impossible unless every category size is a multiple of 4.
usage: python t3_meetings.py n,M [n,M ...]     e.g. 52,4 44,4"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'counting'))
from t3_count import forced_play


def categories(n, pairs):
    beaten = {i: set() for i in range(n)}
    for hi, lo in pairs:
        beaten[lo].add(hi)
    cat = {}

    def get(x):
        if x not in cat:
            cat[x] = 0 if not beaten[x] else 1 + max(get(w) for w in beaten[x])
        return cat[x]
    for x in range(n):
        get(x)
    return cat


for n, M in [tuple(map(int, t.split(','))) for t in sys.argv[1:]]:
    m = n // M; h = (m - 1) // 2
    for a in range(1, h):
        b = h - a
        L, pairs, nn = forced_play(a, b, M)
        cat = categories(nn, pairs)
        k = max(cat.values()) + 1
        sizes = [sum(1 for x in cat if cat[x] == c) for c in range(k)]
        met = {frozenset(p) for p in pairs}
        parts = []
        for c in range(k - 1):
            U = [x for x in cat if cat[x] == c]; W = [x for x in cat if cat[x] == c + 1]
            got = sum(1 for u in U for w in W if frozenset((u, w)) in met)
            parts.append('%s-%s %d/%d' % ('ABCDEFG'[c], 'ABCDEFG'[c + 1], got, len(U) * len(W)))
        print('n=%d (a,b)=(%d,%d) L=%d categories %s sizes %s  meetings %s' % (n, a, b, L, k, sizes, '  '.join(parts)))
