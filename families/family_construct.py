# The family of non-Theorem-3 War cycles, n = 8k+6:
#   player 1: (ABBC)^k        player 2: DE (ABBC)^k CDDE        (letters = Spivey categories, A strongest)
# 1) Letter level: simulate with A>B>C>D>E; reject if two equal letters meet (a tie); check it returns.
# 2) Card level: number the cards (A highest ... E lowest, distinct values), simulate the real game, confirm
#    it never ends (enters a loop), report loop length, winner-run shape and Spivey categories/gaps.
import itertools
from collections import Counter
RANK = {c: i for i, c in enumerate("EDCBA")}          # higher = stronger
def lstep(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    if a == b: return None
    return ((p1[1:] + a + b, p2[1:]) if RANK[a] > RANK[b] else (p1[1:], p2[1:] + b + a))
def cstep(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return ((p1[1:] + (a, b), p2[1:]) if a > b else (p1[1:], p2[1:] + (b, a)))
def letter_cycle(p1, p2):
    s0 = (p1, p2); s = s0; t = 0
    while True:
        s = lstep(s); t += 1
        if s is None: return None, "tie"
        if not s[0] or not s[1]: return None, "ends"
        if s == s0: return t, "cycle"
        if t > 10**6: return None, "no return"
def number(p1, p2):
    cnt = Counter(p1 + p2); vals = {}; v = 1
    for L in "EDCBA":
        vals[L] = list(range(v, v + cnt[L])); v += cnt[L]
    it = {L: iter(vals[L]) for L in vals}
    return tuple(next(it[c]) for c in p1), tuple(next(it[c]) for c in p2)
def card_loop(s):
    seen = {}; t = 0
    while s[0] and s[1]:
        if s in seen: return t - seen[s], s
        seen[s] = t; s = cstep(s); t += 1
    return None, None
def shape(start, n):
    loop = [start]; u = cstep(start)
    while u != start: loop.append(u); u = cstep(u)
    w = [1 if x[0][0] > x[1][0] else 2 for x in loop]
    k = next(i for i in range(len(w)) if w[i] != w[i - 1]); w = w[k:] + w[:k]
    runs = Counter(len(list(g)) for _, g in itertools.groupby(w))
    beats = {}
    for x in loop: beats.setdefault(min(x[0][0], x[1][0]), set()).add(max(x[0][0], x[1][0]))
    cat = {}
    def get(c):
        if c not in cat: cat[c] = 0 if c not in beats else 1 + max(get(b) for b in beats[c])
        return cat[c]
    gaps = Counter(get(min(x[0][0], x[1][0])) - get(max(x[0][0], x[1][0])) for x in loop)
    return dict(runs), dict(gaps), len(set(cat.values()))
for k in range(1, 13):
    p1 = "ABBC" * k; p2 = "DE" + "ABBC" * k + "CDDE"; n = len(p1) + len(p2)
    per, why = letter_cycle(p1, p2)
    line = f"k={k:2d} n={n:3d} (n mod 8 = {n % 8}): letter level {why}" + (f", period {per}" if per else "")
    if why == "cycle":
        L, s = card_loop(number(p1, p2))
        if L:
            runs, gaps, ncat = shape(s, n)
            q, r = divmod(L, n + 2)
            size = f"(= {q} x (n+2))" if r == 0 else "(not a multiple of n+2)"
            line += f" | cards: loop length {L} {size}, runs {runs}, {ncat} categories, loss gaps {gaps}"
        else:
            line += " | cards: the game ends"
    print(line, flush=True)
