"""Tie-free rank assignment for a Theorem-3 shape: give each of the n = 4V slots a rank 1..V, each rank used
exactly 4 times, so that over a full lap every meeting is won by the strictly higher rank (hence no two
cards of one rank ever meet: no battle). Exact depth-first search, top rank first: the slots of the next
rank must be 4 slots that no still-unranked slot beats (such a set is automatically an antichain).
Memoized on the set of unranked slots. Prints a solution or proves there is none.
usage: python tie_free_assign.py n,M [n,M ...]"""
import os, sys
from itertools import combinations
from functools import lru_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'counting'))
from t3_count import forced_play, shape

sys.setrecursionlimit(10000)


def solve(n, pairs):
    beaten_by = [0] * n                      # bitmask of slots that beat slot x
    for hi, lo in pairs:
        beaten_by[lo] |= 1 << hi
    full = (1 << n) - 1

    @lru_cache(maxsize=None)
    def go(rem):
        if rem == 0:
            return ()
        cand = [x for x in range(n) if (rem >> x) & 1 and not (beaten_by[x] & rem)]
        for four in combinations(cand, 4):
            m = sum(1 << x for x in four)
            r = go(rem & ~m)
            if r is not None:
                return (four,) + r
        return None
    return go(full)


for spec in sys.argv[1:]:
    n, M = map(int, spec.split(','))
    m = n // M; h = (m - 1) // 2
    for a in range(1, h):
        b = h - a
        L, pairs, nn = forced_play(a, b, M)
        sol = solve(nn, pairs)
        if sol is None:
            print('n=%d (a,b)=(%d,%d) L=%d: NO tie-free assignment' % (n, a, b, L), flush=True)
        else:
            V = len(sol)
            rank = {}
            for i, four in enumerate(sol):
                for x in four:
                    rank[x] = V - i          # first class found = highest rank
            p1, p2 = shape(a, b, M)
            # replay with ranks only, as real War with natural (winner-first) pickup, checking no tie and the lap
            from collections import deque
            x, y = deque(rank[s] for s in p1), deque(rank[s] for s in p2)
            s0 = (tuple(x), tuple(y)); ties = 0; t = 0
            while True:
                u, w = x.popleft(), y.popleft(); t += 1
                if u == w:
                    ties += 1; break
                (x.extend((u, w)) if u > w else y.extend((w, u)))
                if (tuple(x), tuple(y)) == s0 or t > 10 ** 7:
                    break
            print('n=%d (a,b)=(%d,%d) L=%d: assignment FOUND; replay as real War: back to start after %d tricks, ties %d'
                  % (n, a, b, L, t, ties), flush=True)
            print('    P1:', [rank[s] for s in p1])
            print('    P2:', [rank[s] for s in p2])
