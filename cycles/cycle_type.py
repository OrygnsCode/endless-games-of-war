# Spivey's Question 1: are all War cycles of the Theorem-3 type? Test: around every loop,
# the winners come in runs of exactly 2^v turns (2^v = largest power of 2 dividing n), alternating players.
# Enumerates every distinct cycle via the canonical start set (player 1's top card is n).
import sys, itertools
def step(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return ((p1[1:] + (a, b), p2[1:]) if a > b else (p1[1:], p2[1:] + (b, a)))
def winner(s): return 1 if s[0][0] > s[1][0] else 2
for n in map(int, sys.argv[1:]):
    memo = {}; ncyc = 0; bad = 0; runsets = set()
    v = n & -n
    for perm in itertools.permutations(range(1, n)):
        for j in range(0, n - 1):
            s = ((n,) + perm[:j], perm[j:]); path = []; idx = {}
            while True:
                if s in memo or not s[0] or not s[1]: break
                if s in idx:
                    loop = path[idx[s]:]; ncyc += 1
                    w = [winner(t) for t in loop]
                    # rotate so the loop starts at a change of winner, then take run lengths
                    k = next(i for i in range(len(w)) if w[i] != w[i - 1])
                    w = w[k:] + w[:k]
                    runs = [len(list(g)) for _, g in itertools.groupby(w)]
                    runsets.add(tuple(sorted(set(runs))))
                    if any(r != v for r in runs): bad += 1
                    break
                idx[s] = len(path); path.append(s); s = step(s)
            for t in path: memo[t] = 1
    print(f"n={n}: {ncyc} distinct cycles (P1 holds n); 2^v={v}; run-length sets seen {sorted(runsets)}; NOT Theorem-3 type: {bad}", flush=True)
