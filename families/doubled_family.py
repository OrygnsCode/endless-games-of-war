# Checks the doubled family of cycles for j = 0..5 and k = 1..6, and the family n = 8k + 6 for k <= 40.
# Letters are integers, 0 = A (strongest) to 4 = E, and D(w) interleaves w with w + 1 letter by letter.
# With T = D^j(ABBC), Z = D^j(DE), Y = D^j(CDDE), L = len(T), H = D^j(AB), Q = D^j(BC) and X = H interleaved
# with H + 3, the start is
#     player 1: T^k        player 2: Z T^k Y        n = 2^(j+1) (4k + 3) cards.
# Letter game: no two equal letters may meet; after the first phase of L turns the position must be
# (T^(k-1) X, Q T^(k-1) Y T); after each further phase, (T^(k-1-i) X T^i, Q T^(k-1-i) Y T^(i+1)) for
# i = 1..k-1; and after (k + 1) L turns, the start again, for the first time. The runs of wins must have
# lengths 1 and 2^(j+1) only.
# Card game (n <= 120): number the cards so that every letter beats every later letter; the game must
# cycle, and the cycle length must be a multiple of n + 2^(j+1). Cycles are found with Brent's method.
# A game that neither ends nor repeats within CAP turns is reported as not settled, and is not counted
# as a pass or a failure.
# For j = 0 the start is player 1: (ABBC)^k, player 2: DE (ABBC)^k CDDE. For k <= 40 the letter game must
# pass through S(i) = (BC (ABBC)^(k-1-i) ADBE (ABBC)^i, (ABBC)^(k-i) CDDE (ABBC)^i) after 2 + 4i turns,
# i = 0..k-1, and return to the start for the first time after 4k + 4 turns. For k <= 16 the numbered
# game (numbering as above) is played around its cycle, and each card's Spivey category (0 if the card never
# loses, otherwise one more than the largest category among the cards that beat it) must equal its letter.
import itertools
from collections import Counter

CAP = 20_000_000

def D(w): return [x for c in w for x in (c, c + 1)]
def Dj(w, j):
    for _ in range(j): w = D(w)
    return w
def interleave(u, v): return [x for pair in zip(u, v) for x in pair]
def shift(w, s): return [x + s for x in w]
A, B, C, Dl, E = 0, 1, 2, 3, 4

def letter_step(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    if a == b: return None
    return ((p1[1:] + (a, b), p2[1:]) if a < b else (p1[1:], p2[1:] + (b, a)))   # smaller letter wins

def letter_positions(start, turns):
    """Positions after 0..turns turns (None once equal letters meet or a pile empties) and the winners."""
    s, out, wins = start, [start], []
    for _ in range(turns):
        wins.append(1 if s[0][0] < s[1][0] else 2)
        s = letter_step(s)
        if s is None or not s[0] or not s[1]: return out, wins, False
        out.append(s)
    return out, wins, True

def card_step(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return ((p1[1:] + (a, b), p2[1:]) if a > b else (p1[1:], p2[1:] + (b, a)))

def card_cycle_length(s):
    """Brent: the cycle length, 0 if the game ends, None if not settled within CAP turns."""
    saved, power, lam = s, 1, 0
    for _ in range(CAP):
        s = card_step(s); lam += 1
        if not s[0] or not s[1]: return 0
        if s == saved: return lam
        if lam == power: saved, power, lam = s, power * 2, 0
    return None

def number(start, n):
    cnt = Counter(start[0] + start[1]); it = {}; v = n
    for letter in sorted(cnt):                    # the strongest letter gets the highest numbers
        it[letter] = iter(range(v, v - cnt[letter], -1)); v -= cnt[letter]
    return tuple(next(it[x]) for x in start[0]), tuple(next(it[x]) for x in start[1])

def cyclic_runs(wins):
    c = next(i for i in range(len(wins)) if wins[i] != wins[i - 1])
    return Counter(len(list(g)) for _, g in itertools.groupby(wins[c:] + wins[:c]))

print("Doubled family")
passed = failed = unsettled = 0
for j in range(0, 6):
    for k in range(1, 7):
        T = Dj([A, B, B, C], j); Z = Dj([Dl, E], j); Y = Dj([C, Dl, Dl, E], j); L = len(T)
        H = Dj([A, B], j); Q = Dj([B, C], j); X = interleave(H, shift(H, 3))
        start = (tuple(T * k), tuple(Z + T * k + Y)); n = len(start[0]) + len(start[1])
        period = (k + 1) * L
        pos, wins, alive = letter_positions(start, period)
        phases = alive and pos[L] == (tuple(T * (k - 1) + X), tuple(Q + T * (k - 1) + Y + T))
        for i in range(1, k):
            phases = phases and pos[(i + 1) * L] == (tuple(T * (k - 1 - i) + X + T * i), tuple(Q + T * (k - 1 - i) + Y + T * (i + 1)))
        closed = alive and pos[period] == start and all(p != start for p in pos[1:period])
        runs = cyclic_runs(wins) if closed else Counter()
        ok = phases and closed and set(runs) == {1, 2 ** (j + 1)} and n == 2 ** (j + 1) * (4 * k + 3)
        line = (f"j={j} k={k} n={n:4d}: phases {'OK' if phases else 'FAIL'}, letter cycle {'OK' if closed else 'FAIL'} "
                f"period {period}, runs {dict(runs)}")
        settled = True
        if n <= 120:
            lam = card_cycle_length(number(start, n))
            if lam is None:
                settled = False
                line += f", cards: not settled within {CAP:,} turns"
            elif lam == 0:
                ok = False
                line += ", cards: the game ends"
            else:
                div = lam % (n + 2 ** (j + 1)) == 0
                ok = ok and div
                line += f", cards: cycle of length {lam}, multiple of n+2^(j+1): {div}"
        if not ok: failed += 1
        elif settled: passed += 1
        else: unsettled += 1
        print(line, flush=True)
print(f"passed {passed}, failed {failed}, letter checks passed but card game not settled {unsettled}")

print("Family n = 8k + 6, k = 1..40")
bad = []
for k in range(1, 41):
    ABBC = [A, B, B, C]
    start = (tuple(ABBC * k), tuple([Dl, E] + ABBC * k + [C, Dl, Dl, E]))
    pos, wins, alive = letter_positions(start, 4 * k + 4)
    ok = alive and pos[4 * k + 4] == start and all(p != start for p in pos[1:4 * k + 4])
    for i in range(k):
        S = (tuple([B, C] + ABBC * (k - 1 - i) + [A, Dl, B, E] + ABBC * i), tuple(ABBC * (k - i) + [C, Dl, Dl, E] + ABBC * i))
        ok = ok and pos[2 + 4 * i] == S
    if not ok: bad.append(k)
print(f"every S(i) and the period 4k + 4 as stated, k = 1..40: {not bad}" + (f" (failures at k = {bad})" if bad else ""))

def categories(s, lam):
    """Spivey's category of every card on the card cycle through s (length lam), 0 = A."""
    beaten_by = {}
    for _ in range(lam):
        a, b = s[0][0], s[1][0]
        beaten_by.setdefault(min(a, b), set()).add(max(a, b))
        s = card_step(s)
    cat = {}
    for c in sorted({c for p in s for c in p}, reverse=True):   # every card that beats c is higher
        cat[c] = 1 + max(cat[w] for w in beaten_by[c]) if c in beaten_by else 0
    return cat

bad = []
for k in range(1, 17):
    ABBC = [A, B, B, C]
    start = (tuple(ABBC * k), tuple([Dl, E] + ABBC * k + [C, Dl, Dl, E]))
    cs = number(start, 8 * k + 6)
    lam = card_cycle_length(cs)
    cat = categories(cs, lam) if lam else {}
    letter = dict(zip(cs[0] + cs[1], start[0] + start[1]))
    if not lam or any(cat[c] != letter[c] for c in letter): bad.append(k)
print(f"numbered cycles, k = 1..16: every card's category equals its letter: {not bad}" + (f" (failures at k = {bad})" if bad else ""))
