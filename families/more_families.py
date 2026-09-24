# Checks for the families K(s, t) and F(r, k) and for the six classes of cycles not of Theorem-3 type found by the
# sampler at n = 22. Letter games are played directly; card-level facts (cycle length, Spivey categories, cards that
# never win and their periods) come from one letter period with the cards followed by their starting places, and the
# permutation sigma of the places after one period, so the family checks play no numbered cycle out in full. The
# n = 22 cycles, of at most 1,440 turns, are played in full to read off their categories.
#   K(s, t): player 1 (ABBCADBE)^s ABBC, player 2 DE (ABBCCDDE)^t.
#   F(r, k): player 1 (ABBC)^k U_r, player 2 V_r (ABBC)^k W_r, with U_r = prod_{i=0..r-1} A (D+2i) B (E+2i),
#            V_r = DE + 2r, W_r = prod_{i=0..r} (CDDE + 2i), where w + d moves every letter of w d letters down.
# At the end the numbered cycles of all members with n <= 38 (every letter beating every later letter) are played in full
# to count their categories under Spivey's numerical labeling (Section 3 of his paper: a card is one category below
# the highest-ranked card it loses to).
from math import lcm
LET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ORD = {c: i for i, c in enumerate(LET)}

def lstep(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    if a == b: return None
    return (p1[1:] + a + b, p2[1:]) if ORD[a] < ORD[b] else (p1[1:], p2[1:] + b + a)

def letter_cycle(s, cap):
    """The cycle of the letter game from s, or None if two equal letters meet or a pile empties first."""
    seen, path = {}, []
    for t in range(cap):
        if s in seen: return path[seen[s]:]
        seen[s] = t; path.append(s)
        s = lstep(s)
        if s is None or not s[0] or not s[1]: return None
    return None

def runs(cyc):
    w = [1 if ORD[s[0][0]] < ORD[s[1][0]] else 2 for s in cyc]
    c = next(i for i in range(len(w)) if w[i] != w[i - 1]); r = w[c:] + w[:c]
    out, cur = [], 1
    for i in range(1, len(r)):
        if r[i] == r[i - 1]: cur += 1
        else: out.append(cur); cur = 1
    out.append(cur)
    return sorted(set(out))

def one_period(p1w, p2w):
    """Follow the cards by starting place through one period of the letter cycle through (p1w, p2w)."""
    cyc = letter_cycle((p1w, p2w), 100000)
    assert cyc and (p1w, p2w) in cyc
    P, n = len(cyc), len(p1w) + len(p2w)
    p1 = [(x, q) for q, x in enumerate(p1w)]; p2 = [(x, len(p1w) + q) for q, x in enumerate(p2w)]
    def places(): return {q: (0, d) for d, (_, q) in enumerate(p1)} | {q: (1, d) for d, (_, q) in enumerate(p2)}
    paths = {q: [] for q in range(n)}; meets = []
    for _ in range(P):
        pl = places()
        for q in range(n): paths[q].append(pl[q])
        a, b = p1.pop(0), p2.pop(0)
        w, l = (a, b) if ORD[a[0]] < ORD[b[0]] else (b, a)
        meets.append((w[1], l[1]))
        if w is a: p1 += [a, b]
        else: p2 += [b, a]
    start = {q: (0, q) for q in range(len(p1w))} | {len(p1w) + q: (1, q) for q in range(len(p2w))}
    at = {v: q for q, v in start.items()}
    sigma = {q: at[pl] for q, pl in places().items()}
    return n, cyc, sigma, paths, meets

def orbits(sigma):
    seen, out = set(), []
    for q0 in sigma:
        if q0 in seen: continue
        orb, q = [q0], sigma[q0]
        while q != q0: orb.append(q); q = sigma[q]
        seen |= set(orb); out.append(orb)
    return out

def period(seq):
    m = len(seq)
    return next(p for p in range(1, m + 1) if m % p == 0 and all(seq[i] == seq[(i + p) % m] for i in range(m)))

def card_facts(p1w, p2w):
    """Cycle length, category sizes (A first) and their agreement with the letters, the cards that never win (letters),
    the lengths of their sigma-orbits and their periods. A card keeps its sigma-orbit, so categories are computed on
    orbits: orbit O' beats O when in some turn of the period a place of O' beats a place of O."""
    n, cyc, sigma, paths, meets = one_period(p1w, p2w)
    letters = p1w + p2w; orbs = orbits(sigma); of = {q: i for i, o in enumerate(orbs) for q in o}
    beaten = {i: set() for i in range(len(orbs))}
    for w, l in meets: beaten[of[l]].add(of[w])
    cat = {}
    def get(i):
        if i not in cat: cat[i] = 0 if not beaten[i] else 1 + max(get(j) for j in beaten[i])
        return cat[i]
    for i in range(len(orbs)): get(i)
    sizes = [sum(len(o) for i, o in enumerate(orbs) if cat[i] == c) for c in range(max(cat.values()) + 1)]
    winners = {w for w, _ in meets}
    never = [o for o in orbs if not any(q in winners for q in o)]
    length = len(cyc) * lcm(*[len(o) for o in orbs])
    return dict(n=n, P=len(cyc), length=length, sizes=sizes,
                cat_is_letter=all(cat[of[q]] == ORD[letters[q]] for q in range(n)),
                never_letters="".join(sorted(letters[q] for o in never for q in o)),
                never_orbits=sorted(len(o) for o in never),
                never_periods=sorted({period([pl for q in o for pl in paths[q]]) for o in never}))

def K(s, t): return "ABBCADBE" * s + "ABBC", "DE" + "ABBCCDDE" * t
def shift(w, s): return "".join(LET[ORD[c] + s] for c in w)
def F(r, k):
    U = "".join("A" + shift("D", 2 * i) + "B" + shift("E", 2 * i) for i in range(r))
    V = shift("DE", 2 * r)
    W = "".join(shift("CDDE", 2 * i) for i in range(r + 1))
    return "ABBC" * k + U, V + "ABBC" * k + W

print("Theorem K, s <= 6, 1 <= t <= 6: tie-free, least period 8, runs of 1 and 2; the cards that never win are the")
print("s + t + 1 cards E, on one sigma-orbit, each of period n + 2; the cycle length is a multiple of n + 2")
ok = True
for s in range(0, 7):
    for t in range(1, 7):
        p1w, p2w = K(s, t)
        cyc = letter_cycle((p1w, p2w), 10000)
        f = card_facts(p1w, p2w); n = f["n"]
        good = (cyc is not None and (p1w, p2w) in cyc and len(cyc) == 8 and runs(cyc) == [1, 2] and n == 8 * (s + t) + 6
                and f["never_letters"] == "E" * (s + t + 1) and f["never_orbits"] == [s + t + 1]
                and f["never_periods"] == [n + 2] and f["length"] % (n + 2) == 0)
        ok &= good
        if not good: print("  failure at", s, t, f)
print("  all hold:", ok)

print("Theorem F, r <= 4, k <= 4: tie-free, least period 4(k + r + 1), runs of 1 and 2, n = 8(k + r) + 6; categories")
print("equal the letters (2r + 5 of them); every card that never wins has period n + 2^v; length a multiple of n + 2^v")
ok = True
for r in range(0, 5):
    for k in range(1, 5):
        p1w, p2w = F(r, k)
        cyc = letter_cycle((p1w, p2w), 10000)
        f = card_facts(p1w, p2w); n = f["n"]; v = n & -n
        good = (cyc is not None and (p1w, p2w) in cyc and len(cyc) == 4 * (k + r + 1) and runs(cyc) == [1, 2]
                and n == 8 * (k + r) + 6 and f["cat_is_letter"] and len(f["sizes"]) == 2 * r + 5
                and f["never_periods"] == [n + v] and f["length"] % (n + v) == 0)
        ok &= good
        if not good: print("  failure at", r, k, f)
print("  all hold:", ok)

print("n = 22: the six classes printed by 'sampler 22 10000000 8 22 pos' (first example of each), with the cycle")
print("length and category sizes of the family members, and a doubled position entering each class")
examples = {
    "240": ((19, 17, 18, 8, 13, 12, 6, 2, 22, 15, 16, 7, 11, 9, 4, 1), (14, 10, 21, 5, 20, 3)),
    "288": ((20, 14, 18, 9, 19, 13, 15, 8, 6, 5, 4, 1), (12, 7, 22, 16, 11, 10, 21, 3, 17, 2)),
    "360 (2,3,3,5,4,3,2)": ((10, 13, 4, 21, 14, 19, 9, 16, 3), (1, 22, 20, 18, 15, 17, 12, 11, 6, 8, 7, 5, 2)),
    "360 (3,5,3,3,3,3,2)": ((13, 20, 7, 17, 11, 21, 3, 19, 2), (15, 16, 10, 14, 12, 9, 6, 5, 4, 8, 1, 22, 18)),
    "672": ((3, 19, 17, 14, 9, 10, 6, 8, 1), (18, 16, 7, 22, 5, 12, 2, 20, 15, 13, 11, 21, 4)),
    "1440": ((1, 14, 9, 8, 2, 20, 17, 15, 13), (6, 5, 4, 22, 18, 16, 11, 21, 10, 19, 3, 12, 7)),
}
def cstep(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return (p1[1:] + (a, b), p2[1:]) if a > b else (p1[1:], p2[1:] + (b, a))
def letter_class(s0):
    """The letter cycle of a card cycle, with each card replaced by its Spivey category, in canonical form."""
    loop, u = [s0], cstep(s0)
    while u != s0: loop.append(u); u = cstep(u)
    beaten = {}
    for s in loop: beaten.setdefault(min(s[0][0], s[1][0]), set()).add(max(s[0][0], s[1][0]))
    n = len(s0[0]) + len(s0[1]); cat = {}
    for c in range(n, 0, -1): cat[c] = 1 + max(cat[w] for w in beaten[c]) if c in beaten else 0
    word = lambda p: "".join(LET[cat[c]] for c in p)
    cyc = letter_cycle((word(s0[0]), word(s0[1])), 100000)
    return len(loop), min(min(x, (x[1], x[0])) for x in cyc), cyc
def canon(cyc): return min(min(x, (x[1], x[0])) for x in cyc)
members = {"K(0,2)": K(0, 2), "K(1,1)": K(1, 1), "F(0,2)": F(0, 2), "F(1,1)": F(1, 1)}
member_canon = {name: canon(letter_cycle(w, 10000)) for name, w in members.items()}
def preds(s):
    p1, p2 = s; out = []
    if len(p1) >= 2 and ORD[p1[-2]] < ORD[p1[-1]]: out.append((p1[-2] + p1[:-2], p1[-1] + p2))
    if len(p2) >= 2 and ORD[p2[-2]] < ORD[p2[-1]]: out.append((p2[-1] + p1, p2[-2] + p2[:-2]))
    return [t for t in out if lstep(t) == s]
def doubled(w): return len(w) % 2 == 0 and all(ORD[w[i + 1]] == ORD[w[i]] + 1 for i in range(0, len(w), 2))
for name, s0 in examples.items():
    L, key, cyc = letter_class(s0)
    fam = [m for m, c in member_canon.items() if c == key]
    # nearest doubled position before the cycle whose undoubled words lie on their own tie-free letter cycle
    frontier, seen, found = [(s, 0) for s in cyc], set(cyc), None
    while frontier and found is None:
        nxt = []
        for s, d in frontier:
            for t in preds(s):
                if t in seen: continue
                seen.add(t)
                b = (t[0][::2], t[1][::2])
                if doubled(t[0]) and doubled(t[1]) and b in (letter_cycle(b, 5000) or []):
                    found = (d + 1, t[0][::2], t[1][::2]); break
                nxt.append((t, d + 1))
            if found: break
        frontier = [x for x in nxt if x[1] <= 12]
    print(f"  class {name:20s} length {L:5d}  family member: {', '.join(fam) if fam else 'none':14s}  "
          + (f"doubled position {found[0]} turns before: D({found[1]}) | D({found[2]})" if found else "no doubled position within 12 turns"))
for name, (p1w, p2w) in members.items():
    f = card_facts(p1w, p2w)
    print(f"  {name}: n = {f['n']}, cycle length {f['length']}, category sizes {f['sizes']}")
print("the two doubled bases named in the text: each base is a tie-free 11-card letter cycle, and its doubling leads")
print("into the letter cycle of the class")
def D(w): return "".join(c + LET[ORD[c] + 1] for c in w)
for (b1, b2), name in [(("ADCDAD", "BCDAB"), "1440"), (("ADCF", "BCDEFAD"), "360 (2,3,3,5,4,3,2)")]:
    base = letter_cycle((b1, b2), 5000)
    _, key, _ = letter_class(examples[name])
    s, t, hit = (D(b1), D(b2)), 0, None
    seen = set()
    while s is not None and s[0] and s[1] and s not in seen:
        cyc = letter_cycle(s, 100000)
        if cyc and s in cyc: hit = t; break
        seen.add(s); s = lstep(s); t += 1
    enters = cyc is not None and canon(cyc) == key
    print(f"  base {b1} | {b2}: on its own tie-free letter cycle: {base is not None and (b1, b2) in base}, period {len(base) if base else None}; "
          f"D(base) reaches a cycle after {hit} turns; that cycle is the class {name}: {enters}")
print("n = 22, every listed position ('sampler 22 10000000 8 22 pos 20000000 list', saved in data/sampler_n22_list.txt):")
print("its cycle's category letters are matched against the family members above, and otherwise searched backwards for")
print("a doubled position whose undoubled words lie on their own tie-free letter cycle")
import os
from collections import defaultdict
listing = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sampler_n22_list.txt")
positions = []
for line in open(listing):
    line = line.strip()
    if ":" in line and "|" in line and line.split(":")[0].isdigit():
        a, b = line.split(":", 1)[1].split("|")
        positions.append((tuple(int(x) for x in a.split()), tuple(int(x) for x in b.split())))
def doubled_entry(cyc):
    frontier, seen = [(s, 0) for s in cyc], set(cyc)
    while frontier:
        nxt = []
        for s, d in frontier:
            for t in preds(s):
                if t in seen: continue
                seen.add(t)
                b = (t[0][::2], t[1][::2])
                if doubled(t[0]) and doubled(t[1]) and b in (letter_cycle(b, 5000) or []): return d + 1
                if d + 1 < 12: nxt.append((t, d + 1))
        frontier = nxt
    return None
cache = {}
table = defaultdict(lambda: defaultdict(int)); keys = defaultdict(set)
for s0 in positions:
    L, key, cyc = letter_class(s0)
    sizes = ",".join(str(sum(w.count(LET[c]) for w in key)) for c in range(max(ORD[x] for w in key for x in w) + 1))
    if key not in cache:
        fam = [m for m, c in member_canon.items() if c == key]
        cache[key] = fam[0] if fam else (f"doubled 11-card base, {doubled_entry(cyc)} turns before" if doubled_entry(cyc) else "none found")
    table[(L, sizes)][cache[key]] += 1; keys[(L, sizes)].add(key)
print(f"  {len(positions)} positions")
for (L, sizes) in sorted(table):
    print(f"  length {L:5d}, sizes {sizes:15s}: {len(keys[(L, sizes)])} letter cycle(s); "
          + "; ".join(f"{v} {k}" for k, v in sorted(table[(L, sizes)].items())))
print("Spivey's numerical labeling: numbered cycles of members with n <= 38, every letter beating every later letter,")
print("played in full; categories under the definition used here and under the numerical labeling, and the run lengths")
def numbered(p1w, p2w):
    letters = p1w + p2w; n = len(letters)
    order = sorted(range(n), key=lambda q: (ORD[letters[q]], q))
    num = {q: n - i for i, q in enumerate(order)}
    return tuple(num[q] for q in range(len(p1w))), tuple(num[len(p1w) + q] for q in range(len(p2w)))
members38 = {}
for N in range(1, 5):
    for s in range(N): members38.setdefault(K(s, N - s), f"K({s},{N - s})")
    for r in range(N): members38.setdefault(F(r, N - r), f"F({r},{N - r})")
print(f"  {len(members38)} members (K(0,1) = F(0,1)), on "
      f"{len({canon(letter_cycle(w, 10000)) for w in members38})} different letter cycles")
for (p1w, p2w), name in members38.items():
    s0 = numbered(p1w, p2w); n = len(p1w) + len(p2w)
    loop, u = [s0], cstep(s0)
    while u != s0: loop.append(u); u = cstep(u)
    beaten = {}
    for x in loop: beaten.setdefault(min(x[0][0], x[1][0]), set()).add(max(x[0][0], x[1][0]))
    first, numeric = {}, {}
    for c in range(n, 0, -1):
        first[c] = 1 + max(first[w] for w in beaten[c]) if c in beaten else 0
        numeric[c] = 1 + numeric[max(beaten[c])] if c in beaten else 0
    wins = [1 if x[0][0] > x[1][0] else 2 for x in loop]
    c0 = next(i for i in range(len(wins)) if wins[i] != wins[i - 1]); w = wins[c0:] + wins[:c0]
    lens, cur = set(), 1
    for i in range(1, len(w)):
        if w[i] == w[i - 1]: cur += 1
        else: lens.add(cur); cur = 1
    lens.add(cur)
    print(f"  {name}: n = {n}, length {len(loop)}, categories {max(first.values()) + 1} (Section 2) and "
          f"{max(numeric.values()) + 1} (numerical labeling), runs of wins {sorted(lens)}")
print("Reachability of the cycles of Theorem F, r, k <= 4, every letter beating every later letter: after the first two")
print("turns player 1 holds n/2 - 1 cards and player 2's pile ends with (D+2r)(E+2r); undoing one win of player 2 gives")
print("a deal with n/2 cards each, not on the cycle, that enters it after one turn")
ok = True
for r in range(0, 5):
    for k in range(1, 5):
        p1w, p2w = F(r, k); n = len(p1w) + len(p2w)
        s0 = numbered(p1w, p2w); letter = dict(zip(s0[0] + s0[1], p1w + p2w))
        a, b = cstep(cstep(s0))
        x, y = b[-2], b[-1]
        deal = ((y,) + a, (x,) + b[:-2])
        good = (len(a) == n // 2 - 1 and letter[x] + letter[y] == shift("DE", 2 * r) and x > y
                and len(deal[0]) == len(deal[1]) == n // 2 and cstep(deal) == (a, b))
        u = cstep((a, b))
        while u != (a, b):
            good &= u != deal; u = cstep(u)
        ok &= good
        if not good: print("  failure at", r, k)
print("  all hold:", ok)
