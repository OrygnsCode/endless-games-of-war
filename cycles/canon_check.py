# Test: scanning only positions where player 1's top card is n finds every cycle of War.
# Argument: card n never loses, so its holder keeps it; every infinite game brings n to the
# top of its holder's pile; swapping players maps cycles to cycles, so WLOG the holder is P1.
# Compare with a scan of every position (both piles nonempty), for small n.
import sys, itertools
def step(s):
    p1, p2 = s
    a, b = p1[0], p2[0]
    if a > b: p1, p2 = p1[1:] + (a, b), p2[1:]
    else:     p1, p2 = p1[1:], p2[1:] + (b, a)
    return (p1, p2)
def cycles_from(starts):
    status = {}                      # state -> 'E' (ends) or cycle id
    cyc = {}                         # cycle id -> frozenset of states
    for s0 in starts:
        path, idx, s = [], {}, s0
        while True:
            if s in status: res = status[s]; break
            if not s[0] or not s[1]: res = 'E'; break
            if s in idx:              # new cycle found
                cid = len(cyc); cyc[cid] = frozenset(path[idx[s]:]); res = cid; break
            idx[s] = len(path); path.append(s); s = step(s)
        for t in path: status[t] = res
    return {c for c in cyc.values()}
def swap(c): return frozenset((q, p) for p, q in c)
def canon_set(cs):                   # identify a cycle with its player-swapped twin
    return {min(c, swap(c), key=lambda z: sorted(z)) for c in cs}
for n in range(1, int(sys.argv[1]) + 1):
    cards = range(1, n + 1)
    allstates = [(perm[:j], perm[j:]) for perm in itertools.permutations(cards) for j in range(1, n)]
    canon = [((n,) + perm[:j], perm[j:]) for perm in itertools.permutations(range(1, n)) for j in range(0, n - 1)]
    deals = [(perm[:(n + 1) // 2], perm[(n + 1) // 2:]) for perm in itertools.permutations(cards)] if n > 1 else []
    A, Cn = cycles_from(allstates), cycles_from(canon)
    D = cycles_from(deals)
    ok = canon_set(A) == canon_set(Cn)
    print(f"n={n}: states all={len(allstates)} canon={len(canon)} | distinct cycles all={len(A)} "
          f"canon-scan={len(Cn)} (up to swap: {len(canon_set(A))} vs {len(canon_set(Cn))}) same={ok} | "
          f"cycles reachable from deals={len(D)}", flush=True)
