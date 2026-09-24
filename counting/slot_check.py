"""Strict check of the slot model: for n = 5, 7, 9 and every (a, b), label the slots with all n! value
assignments and play each position until it ends or repeats a position. Claim: the start lies on a cycle
iff the labeling is a linear extension of P_{a,b}, and then its first return is after exactly L turns."""
import math
from collections import deque
from itertools import permutations
from odd_count import poset, build


def on_cycle(p1, p2):
    x, y = deque(p1), deque(p2)
    start = (tuple(x), tuple(y))
    seen = {start: 0}
    t = 0
    while True:
        c, d = x.popleft(), y.popleft()
        if c > d:
            x.extend((c, d))
        else:
            y.extend((d, c))
        t += 1
        if not x or not y:
            return None
        st = (tuple(x), tuple(y))
        if st in seen:
            return t if seen[st] == 0 else None   # start on the cycle iff the first repeat is the start
        seen[st] = t


for n in (5, 7, 9):
    h = (n - 1) // 2
    for a in range(1, h):
        b = h - a
        m, rel = poset(a, b)
        L = math.lcm(n + 1, 2 * a, 2 * b)
        ext = cyc_ext = cyc_other = 0
        for perm in permutations(range(1, n + 1)):
            val = dict(enumerate(perm))
            ok = all(val[hi] > val[lo] for hi, lo in rel)
            r = on_cycle(*build(a, b, val))
            if ok:
                ext += 1
                assert r == L, (n, a, b, perm, r)
                cyc_ext += 1
            elif r is not None:
                cyc_other += 1
        print("n=%d (a,b)=(%d,%d): %d extensions, all on a cycle of length %d; other labelings on a cycle: %d"
              % (n, a, b, ext, L, cyc_other), flush=True)
