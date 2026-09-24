"""Count the cycles of single-suit War for odd n from the slot model, and check the model by play.

For odd n (Spivey Thm 6) a cycle, at a moment when player 1 is about to win, looks like
  player 1: A B A B ... (2a cards),  player 2: B A B A ... B (2b+1 cards),  a, b >= 1, a + b = (n-1)/2,
every turn an A card beats a B card, and the players alternate winning. Index the turns 2s (player 1 wins) and
2s+1 (player 2 wins). Player 1's A cards come up in the cyclic order A_0..A_{a-1} (A_{s mod a} at turn 2s),
player 2's A' cards as A'_{s mod b} at turn 2s+1, and the B cards as B_{s mod (a+b+1)} at turn 2s (played by
player 2) and B_{(s-a) mod (a+b+1)} at turn 2s+1 (played by player 1).
So A_i meets B_j iff i = j mod gcd(a, a+b+1), and A'_i meets B_j iff i = j + a mod gcd(b, a+b+1).
A position of this shape is on a cycle iff every A card is higher than every B card it meets, so the number of
such positions is the number of linear extensions e(a, b) of that poset, and the number of cycles with
parameters (a, b), counting a cycle and its exchange separately, is e(a, b) / (L/2), L = lcm(n+1, 2a, 2b).
It also builds the positions explicitly for small n and plays them, to check the slot bookkeeping.
"""
import math
import sys
from functools import lru_cache
from itertools import permutations


def poset(a, b):
    """elements 0..n-1: A_0..A_{a-1}, A'_0..A'_{b-1}, B_0..B_{a+b}; returns list of (hi, lo) pairs"""
    nb = a + b + 1
    A = list(range(a)); A2 = list(range(a, a + b)); B = list(range(a + b, a + b + nb))
    g1, g2 = math.gcd(a, nb), math.gcd(b, nb)
    rel = []
    for i in range(a):
        for j in range(nb):
            if (i - j) % g1 == 0:
                rel.append((A[i], B[j]))
    for i in range(b):
        for j in range(nb):
            if (i - j - a) % g2 == 0:
                rel.append((A2[i], B[j]))
    return 2 * a + 2 * b + 1, rel


def linext(n, rel):
    below = [0] * n          # mask of the elements that must be lower than x
    for hi, lo in rel:
        below[hi] |= 1 << lo
    # assign values 1, 2, ... from the bottom: x can take the next value once everything below it is placed
    @lru_cache(maxsize=None)
    def f(mask):
        if mask == (1 << n) - 1:
            return 1
        t = 0
        for x in range(n):
            if not (mask >> x) & 1 and (below[x] & ~mask) == 0:
                t += f(mask | (1 << x))
        return t
    return f(0)


def counts(n):
    assert n % 2 == 1 and n >= 5
    h = (n - 1) // 2
    out = []
    for a in range(1, h):
        b = h - a
        m, rel = poset(a, b)
        e = linext(m, rel)
        L = math.lcm(n + 1, 2 * a, 2 * b)
        assert e % (L // 2) == 0, (n, a, b, e, L)
        out.append((a, b, e, L, e // (L // 2)))
    return out


# ---- explicit check by playing: build the position for given slot values and verify it repeats ----
def build(a, b, val):
    """val: dict element -> card value. Returns (pile1, pile2) at turn 0 (player 1 about to win)."""
    nb = a + b + 1
    A = lambda i: val[i % a]
    A2 = lambda i: val[a + i % b]
    B = lambda j: val[a + b + j % nb]
    # player 1 plays A_s at turn 2s and B_{s-a} at turn 2s+1, for s = 0..a-1 (all 2a cards)
    p1 = []
    for s in range(a):
        p1 += [A(s), B(s - a)]
    # player 2 plays B_s at turn 2s and A'_s at turn 2s+1, for s = 0..b, but only 2b+1 cards
    p2 = []
    for s in range(b + 1):
        p2.append(B(s))
        if s < b:
            p2.append(A2(s))
    return p1, p2


def play(p1, p2, limit):
    from collections import deque
    x, y = deque(p1), deque(p2)
    start = (tuple(x), tuple(y))
    for t in range(1, limit + 1):
        c, d = x.popleft(), y.popleft()
        if c > d:
            x.extend((c, d))
        else:
            y.extend((d, c))
        if not x or not y:
            return None
        if (tuple(x), tuple(y)) == start:
            return t
    return -1


if __name__ == "__main__":
    # self-check of the slot model for n = 5, 7, 9: every linear extension gives a position that returns
    # after exactly L turns, and every non-extension gives one that does not stay on this pattern
    for n in (5, 7, 9):
        h = (n - 1) // 2
        for a in range(1, h):
            b = h - a
            m, rel = poset(a, b)
            L = math.lcm(n + 1, 2 * a, 2 * b)
            good = bad = 0
            for perm in permutations(range(1, n + 1)):
                val = dict(enumerate(perm))
                ok = all(val[hi] > val[lo] for hi, lo in rel)
                p1, p2 = build(a, b, val)
                r = play(p1, p2, L)
                if ok:
                    assert r == L, (n, a, b, perm, r, L)
                    good += 1
                else:
                    assert r != L, (n, a, b, perm)
                    bad += 1
            print("n=%d (a,b)=(%d,%d): %d extensions all cycle with length %d; %d others do not" % (n, a, b, good, L, bad))
    for n in range(5, int(sys.argv[1]) + 1 if len(sys.argv) > 1 else 16, 2):
        rows = counts(n)
        tot = sum(r[4] for r in rows)
        print("n=%2d  cycles, each exchange counted separately = %d (up to exchange: %d)   by (a,b): %s"
              % (n, tot, tot // 2, "  ".join("(%d,%d):e=%d L=%d c=%d" % r for r in rows)))
