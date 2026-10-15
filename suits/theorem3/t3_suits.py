# Cycles of Theorem-3 type with suits.
# For n = m * 2^v (m >= 5 odd, M = 2^v) and each shape a + b = (m-1)/2 this builds the forced-play position (player 1:
# a groups of 2M places; player 2: the last M places of a group, then b groups; the letter of place i is the number
# of 1s of i, 0 = strongest), follows the cards by their starting places over a full cycle of the place permutation,
# and reports the level sizes, whether every card of each level meets every card of the next one, and whether a deck
# with s suits (n/s ranks of s cards) can be ranked so that every meeting is won by a strictly higher rank.
# If the levels meet completely, s must divide every level size, and the top and bottom levels have h and h + 1
# cards, so no ranking exists for s >= 2; otherwise a SAT solver decides.
#   python t3_suits.py 28 44 52 60       (every shape)
#   python t3_suits.py 68:2               (one shape, a = 2)
import sys
from math import lcm

def popc(i): return bin(i).count("1")

def forced(n, a):
    v = (n & -n).bit_length() - 1; M, m = 2 ** v, n >> v; b = (m - 1) // 2 - a
    s1 = [popc(i) for _ in range(a) for i in range(2 * M)]
    s2 = [popc(i) for i in range(M, 2 * M)] + [popc(i) for _ in range(b) for i in range(2 * M)]
    return s1, s2

def meetings(s1, s2):
    # (winner, loser) pairs of cards, by starting place, over a full cycle; None if equal letters meet
    n, n1 = len(s1) + len(s2), len(s1)
    p1 = [(x, q) for q, x in enumerate(s1)]; p2 = [(x, n1 + q) for q, x in enumerate(s2)]
    meets = []
    while True:
        a, b = p1.pop(0), p2.pop(0)
        if a[0] == b[0]: return None
        w, l = (a, b) if a[0] < b[0] else (b, a)
        meets.append((w[1], l[1]))
        if w is a: p1 += [a, b]
        else: p2 += [b, a]
        if not p1 or not p2: return None
        if [x for x, _ in p1] == s1 and [x for x, _ in p2] == s2: break
    start = {q: (0, q) for q in range(n1)} | {n1 + q: (1, q) for q in range(len(s2))}
    at = {v: q for q, v in start.items()}
    now = {q: (0, d) for d, (_, q) in enumerate(p1)} | {q: (1, d) for d, (_, q) in enumerate(p2)}
    pi = {q: at[now[q]] for q in range(n)}
    seen, lens = set(), []
    for q0 in range(n):
        if q0 in seen: continue
        q, k = q0, 0
        while True:
            seen.add(q); q = pi[q]; k += 1
            if q == q0: break
        lens.append(k)
    inv = {v: q for q, v in pi.items()}
    pairs, back = set(), list(range(n))
    for _ in range(lcm(*lens)):
        for w, l in meets: pairs.add((back[w], back[l]))
        back = [back[inv[q]] for q in range(n)]
    return pairs

def complete(pairs, letter):
    # beats only go from a level to the next, so the order is complete iff adjacent levels meet completely
    size = {j: letter.count(j) for j in set(letter)}
    met = {}
    for w, l in pairs: met[letter[w]] = met.get(letter[w], 0) + 1
    return all(met.get(j, 0) == size[j] * size[j + 1] for j in size if j + 1 in size)

def rankable(pairs, n, s):
    # y(i, k) = "rank of card i is at least k"; x(i, k) = "rank of card i is exactly k"
    from pysat.formula import CNF, IDPool
    from pysat.card import CardEnc, EncType
    from pysat.solvers import Glucose4
    V = n // s; pool = IDPool(); cnf = CNF()
    y = lambda i, k: pool.id(("y", i, k))
    for i in range(n):
        for k in range(1, V - 1): cnf.append([-y(i, k + 1), y(i, k)])
    for w, l in pairs:                                   # rank(w) >= rank(l) + 1
        cnf.append([y(w, 1)])
        for k in range(1, V - 1): cnf.append([-y(l, k), y(w, k + 1)])
        cnf.append([-y(l, V - 1)])
    for k in range(V):                                   # exactly s cards of each rank
        xs = []
        for i in range(n):
            xi = pool.id(("x", i, k)); xs.append(xi)
            lo = [y(i, k)] if k >= 1 else []; hi = [y(i, k + 1)] if k + 1 <= V - 1 else []
            if lo: cnf.append([-xi, lo[0]])
            if hi: cnf.append([-xi, -hi[0]])
            cnf.append([xi] + [-u for u in lo] + hi)
        cnf.extend(CardEnc.equals(lits=xs, bound=s, vpool=pool, encoding=EncType.seqcounter).clauses)
    with Glucose4(bootstrap_with=cnf.clauses) as S:
        return "yes" if S.solve() else "no"

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        n, _, only = arg.partition(":"); n = int(n)
        v = (n & -n).bit_length() - 1; m = n >> v; h = (m - 1) // 2
        if m < 5: print(f"n={n}: no cycles of Theorem-3 type (m = {m})"); continue
        for a in ([int(only)] if only else range(1, h)):
            s1, s2 = forced(n, a); letter = s1 + s2
            pairs = meetings(s1, s2)
            sizes = [letter.count(j) for j in range(v + 2)]
            comp = complete(pairs, letter)
            out = f"n={n} shape ({a},{h - a}): level sizes {sizes}, complete: {comp}"
            for s in (2, 4):
                if n % s: continue
                if comp: out += f", {s} suits: no (complete)"
                else: out += f", {s} suits: {rankable(pairs, n, s)}"
            print(out, flush=True)
