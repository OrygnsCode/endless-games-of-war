# Follows the cards of the doubled family's letter cycle by their starting places.
# Letters are integers, 0 = A (strongest); D(w) interleaves w with w + 1 letter by letter. With
# T = D^j(ABBC), Z = D^j(DE), Y = D^j(CDDE), the start is player 1: T^k, player 2: Z T^k Y, and the letter
# game returns to it after P = 2^(j+2) (k+1) turns with no two equal letters meeting.
# In any numbered cycle that follows this letter game, where a card goes depends only on its starting place,
# so one period of the letter game gives, for every place q, the places visited in P turns and the place
# pi(q) reached at the end. The meetings over a full cycle of pi give the order "winner above loser" that a
# numbering must respect, and the cards that never win are the ones that can be card 1.
# Part 1: for every member with n <= 255, which cards never win, and the period of each.
# Part 2: n = 14 (j = 0, k = 1): all numberings that respect the order, the cycles they give, and their lengths.
from collections import Counter
from functools import lru_cache
from math import lcm

def D(w): return [x for c in w for x in (c, c + 1)]
def Dj(w, j):
    for _ in range(j): w = D(w)
    return w

def one_period(j, k):
    T = Dj([0, 1, 1, 2], j); Z = Dj([3, 4], j); Y = Dj([2, 3, 3, 4], j)
    s1, s2 = T * k, Z + T * k + Y
    n, P = len(s1) + len(s2), 2 ** (j + 2) * (k + 1)
    p1 = [(x, q) for q, x in enumerate(s1)]
    p2 = [(x, len(s1) + q) for q, x in enumerate(s2)]
    def places():
        return {q: (0, d) for d, (_, q) in enumerate(p1)} | {q: (1, d) for d, (_, q) in enumerate(p2)}
    paths = {q: [] for q in range(n)}; winners = set(); meets = []
    for _ in range(P):
        pl = places()
        for q in range(n): paths[q].append(pl[q])
        a, b = p1.pop(0), p2.pop(0)
        assert a[0] != b[0], "equal letters met"
        w, l = (a, b) if a[0] < b[0] else (b, a)
        winners.add(w[1]); meets.append((w[1], l[1]))
        if w is a: p1 += [a, b]
        else: p2 += [b, a]
    assert [x for x, _ in p1] == s1 and [x for x, _ in p2] == s2, "letter game did not return in P turns"
    start = {q: (0, q) for q in range(len(s1))} | {len(s1) + q: (1, q) for q in range(len(s2))}
    at = {v: q for q, v in start.items()}
    pi = {q: at[pl] for q, pl in places().items()}
    return n, P, len(s1), s1 + s2, pi, paths, winners, meets

def orbits(pi):
    seen, out = set(), []
    for q0 in pi:
        if q0 in seen: continue
        orb, q = [q0], pi[q0]
        while q != q0: orb.append(q); q = pi[q]
        seen |= set(orb); out.append(orb)
    return out

def period(seq):
    m = len(seq)
    return next(p for p in range(1, m + 1) if m % p == 0 and all(seq[i] == seq[(i + p) % m] for i in range(m)))

print("Part 1: period of every card that never wins, members with n <= 255")
all_ok, set_ok, by_letter, members = True, True, Counter(), 0
for j in range(5):
    for k in range(1, 32):
        n = 2 ** (j + 1) * (4 * k + 3)
        if n > 255: continue
        members += 1
        n, P, n1, letters, pi, paths, winners, meets = one_period(j, k)
        # expected: the last cards of Z and of Y, and the last card of each of both players' first k - 1 copies of T
        L = 4 * 2 ** j
        expected = {n1 + L // 2 - 1, n - 1} | {i * L - 1 for i in range(1, k)} | {n1 + L // 2 + i * L - 1 for i in range(1, k)}
        never = {q for orb in orbits(pi) if not any(q2 in winners for q2 in orb) for q in orb}
        if never != expected or any(pi[q] == q or pi[pi[q]] != q for q in expected):
            set_ok = False
            print(f"  j={j} k={k} n={n}: the cards that never win are not the expected ones")
        for orb in orbits(pi):
            if any(q in winners for q in orb): continue
            by_letter["ABCDEFGHI"[letters[orb[0]]]] += 1
            p = period([pl for q in orb for pl in paths[q]])
            if p != n + (n & -n):
                all_ok = False
                print(f"  j={j} k={k} n={n}: a card of letter {'ABCDEFGHI'[letters[orb[0]]]} has period {p}, not {n + (n & -n)}")
print(f"  {members} members; orbits of cards that never win, by letter: {dict(sorted(by_letter.items()))}")
print("  the cards that never win are the last cards of Z, of Y and of both players' first k - 1 copies of T,")
print(f"  and each lies on a 2-cycle of pi: {set_ok}")
print(f"  every card that never wins has period n + 2^v: {all_ok}")

print("Part 2: n = 14")
n, P, n1, letters, pi, paths, winners, meets = one_period(0, 1)
order_pi = 1
for orb in orbits(pi): order_pi = lcm(order_pi, len(orb))
inv = {v: q for q, v in pi.items()}
above = [0] * n                    # above[x]: the cards that must get higher numbers than card x
back = list(range(n))              # back[q]: starting place of the card at place q, in the current period
for _ in range(order_pi):
    for w, l in meets: above[back[l]] |= 1 << back[w]
    back = [back[inv[q]] for q in range(n)]

@lru_cache(None)
def count(mask):                   # numbers are given from the top down; mask = places already numbered
    if mask == (1 << n) - 1: return 1
    return sum(count(mask | 1 << x) for x in range(n) if not mask >> x & 1 and above[x] & ~mask == 0)

def numberings(mask, order):
    if mask == (1 << n) - 1: yield order; return
    for x in range(n):
        if not mask >> x & 1 and above[x] & ~mask == 0: yield from numberings(mask | 1 << x, order + [x])

def step(s):
    a, b = s[0][0], s[1][0]
    return ((s[0][1:] + (a, b), s[1][1:]) if a > b else (s[0][1:], s[1][1:] + (b, a)))

cycles, lengths, total = set(), Counter(), 0
for order in numberings(0, []):
    total += 1
    num = {q: n - i for i, q in enumerate(order)}
    s = (tuple(num[q] for q in range(n1)), tuple(num[q] for q in range(n1, n)))
    loop, u = [s], step(s)
    while u != s: loop.append(u); u = step(u)
    cycles.add(min(min(x, (x[1], x[0])) for x in loop))
    lengths[len(loop)] += 1
print(f"  letter period {P}; the cards return to their places after {order_pi} periods")
print(f"  numberings that respect the order: {count(0)} (enumerated: {total})")
print(f"  distinct cycles, counting a cycle and its exchange as one: {len(cycles)}; lengths over all numberings: {dict(lengths)}")
