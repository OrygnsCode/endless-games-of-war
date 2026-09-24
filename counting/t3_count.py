"""Count the cycles of Spivey's Theorem-3 type for any n = m * 2^v, m odd. No search over positions.

Spivey Thms 11-13: in such a cycle the players alternate winning M = 2^v turns (M is forced by n), and at the
start of a block won by player 1, player 1 holds a groups of 2M cards and player 2 holds M cards followed by b groups
of 2M, with a, b >= 1 and 2a + 2b + 1 = m. Each group starts with an A card.
So every such position is a labeling of a fixed set of n slots. Play the forced schedule (player 1 wins M, player 2
wins M, ...) on the slot labels until the labeled position returns, and record who beats whom. A labeling lies on
such a cycle iff every recorded winner gets a higher value than its loser, i.e. iff it is a linear extension of the
recorded order. Each cycle of shape (a, b) and length L has exactly L/(2M) positions at the start of a player-1 block;
exchanging the players maps shape (a, b) to (b, a) and never fixes a cycle. Hence
    D3(n) = sum_a M * e(a, b) / L(a, b).
For M = 1 (odd n) this is the count computed by odd_formula.py.
"""
import math
import sys
from collections import deque
from fractions import Fraction
from functools import lru_cache


def shape(a, b, M):
    p1 = list(range(2 * M * a))
    p2 = list(range(2 * M * a, 2 * M * a + M * (2 * b + 1)))
    return p1, p2


def forced_play(a, b, M):
    p1, p2 = shape(a, b, M)
    x, y = deque(p1), deque(p2)
    start = (tuple(x), tuple(y))
    pairs = set()
    t = 0
    while True:
        for who in (0, 1):
            for _ in range(M):
                c, d = x.popleft(), y.popleft()
                if who == 0:
                    pairs.add((c, d)); x.extend((c, d))
                else:
                    pairs.add((d, c)); y.extend((d, c))
                t += 1
                assert x and y
        if (tuple(x), tuple(y)) == start:
            return t, pairs, len(p1) + len(p2)


def linext(n, pairs):
    below = [0] * n
    for hi, lo in pairs:
        below[hi] |= 1 << lo
    full = (1 << n) - 1
    # iterative DP over subsets placed from the bottom (values 1, 2, ...)
    f = {0: 1}
    for size in range(n):
        g = {}
        for mask, cnt in f.items():
            for x in range(n):
                if not (mask >> x) & 1 and (below[x] & ~mask) == 0:
                    nm = mask | (1 << x)
                    g[nm] = g.get(nm, 0) + cnt
        f = g
    return f.get(full, 0)


def D3(n, verbose=True):
    v = (n & -n).bit_length() - 1
    M = 1 << v
    m = n // M
    h = (m - 1) // 2
    total = Fraction(0)
    rows = []
    for a in range(1, h):
        b = h - a
        L, pairs, nn = forced_play(a, b, M)
        assert nn == n
        e = linext(n, pairs)
        rows.append((a, b, L, e))
        total += Fraction(M * e, L)
    assert total.denominator == 1
    return M, rows, int(total)


if __name__ == "__main__":
    for n in [int(t) for t in sys.argv[1:]]:
        M, rows, tot = D3(n)
        print("n=%d M=%d: %s  D3=%s" % (n, M, "  ".join("(a,b)=(%d,%d) L=%d e=%d" % r for r in rows), tot), flush=True)
