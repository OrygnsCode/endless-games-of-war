# Period of card 1 (the lowest card) in cycles not of Theorem-3 type, compared with n + 2^v: the family
# n = 8k + 6 for k <= 8, doubled members (j = 1, k <= 3; j = 2, k = 1), and the first example of each of the
# six classes of such cycles at n = 22 printed by 'sampler 22 10000000 8 22 pos' (samples 305173, 9883,
# 5116227, 524086, 19832, 399258).
from collections import Counter
def step(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return ((p1[1:] + (a, b), p2[1:]) if a > b else (p1[1:], p2[1:] + (b, a)))
def D(w): return [x for c in w for x in (c, c + 1)]
def Dj(w, j):
    for _ in range(j): w = D(w)
    return w
def number(l1, l2):
    n = len(l1) + len(l2); cnt = Counter(l1 + l2); it = {}; v = n
    for L in sorted(cnt): it[L] = iter(range(v, v - cnt[L], -1)); v -= cnt[L]
    return tuple(next(it[x]) for x in l1), tuple(next(it[x]) for x in l2)
def enter_loop(s):
    seen = {}; t = 0
    while s not in seen: seen[s] = t; s = step(s); t += 1
    return s, t - seen[s]
def card1_period(s, L):
    # positions of card 1 along the loop; minimal period dividing L
    pos = []
    u = s
    for _ in range(L):
        p1, p2 = u
        pos.append((0, p1.index(1)) if 1 in p1 else (1, p2.index(1)))
        u = step(u)
    return next(p for p in range(1, L + 1) if L % p == 0 and all(pos[i] == pos[(i + p) % L] for i in range(L)))
cases = []
for k in range(1, 9):
    cases.append((f"family k={k}", number([0,1,1,2]*k, [3,4] + [0,1,1,2]*k + [2,3,3,4])))
for j, ks in ((1, (1, 2, 3)), (2, (1,))):
    for k in ks:
        T = Dj([0,1,1,2], j); Z = Dj([3,4], j); Y = Dj([2,3,3,4], j)
        cases.append((f"doubled j={j} k={k}", number(T*k, Z + T*k + Y)))
cases.append(("sampler n=22 #305173", ((19, 17, 18, 8, 13, 12, 6, 2, 22, 15, 16, 7, 11, 9, 4, 1), (14, 10, 21, 5, 20, 3))))
cases.append(("sampler n=22 #9883", ((20, 14, 18, 9, 19, 13, 15, 8, 6, 5, 4, 1), (12, 7, 22, 16, 11, 10, 21, 3, 17, 2))))
cases.append(("sampler n=22 #5116227", ((10, 13, 4, 21, 14, 19, 9, 16, 3), (1, 22, 20, 18, 15, 17, 12, 11, 6, 8, 7, 5, 2))))
cases.append(("sampler n=22 #524086", ((13, 20, 7, 17, 11, 21, 3, 19, 2), (15, 16, 10, 14, 12, 9, 6, 5, 4, 8, 1, 22, 18))))
cases.append(("sampler n=22 #19832", ((3, 19, 17, 14, 9, 10, 6, 8, 1), (18, 16, 7, 22, 5, 12, 2, 20, 15, 13, 11, 21, 4))))
cases.append(("sampler n=22 #399258", ((1, 14, 9, 8, 2, 20, 17, 15, 13), (6, 5, 4, 22, 18, 16, 11, 21, 10, 19, 3, 12, 7))))
ok = True
for name, s in cases:
    n = len(s[0]) + len(s[1]); v = n & -n
    s, L = enter_loop(s)
    p = card1_period(s, L)
    ok &= (p == n + v)
    print(f"{name:24s} n={n:3d} L={L:7d}  card-1 period {p}  n+2^v={n+v}  equal: {p == n+v}", flush=True)
print("all equal:", ok)
