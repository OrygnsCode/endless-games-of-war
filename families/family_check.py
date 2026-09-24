"""Check of the infinite family of War cycles that are not of Spivey's Theorem-3 type, n = 8k+6.
It shares no code with family_construct.py.

Claim: for n = 8k+6, the category-level position
    player 1: (ABBC)^k      player 2: DE (ABBC)^k CDDE        (A strongest ... E weakest)
(1) cycles at the letter level with no turn between equal letters,
(2) so any numbering of the cards consistent with the letters gives a real War game that never ends
    (Spivey's Lemma 1: when equal letters never meet, every outcome is decided by the letters),
(3) and that cycle is not of Spivey's Theorem-3 type.

Checks:
  a) letter game: returns to start? no ties ever? letter period?
  b) card game (A cards highest ... E cards lowest, several different numberings): loop found by a
     seen-dict, loop length, start is on the loop, winner-run lengths around the loop
  c) Spivey categories recomputed from the card game's actual losses (p.749: cat = 1 + max cat of
     the cards that beat it) and the set of category gaps (loser cat - winner cat)

  python family_check.py 12
"""
import random
import sys
from collections import deque, defaultdict

RANK = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}


def letter_position(k):
    return list("ABBC" * k), list("DE" + "ABBC" * k + "CDDE")


def play_letters(p1, p2, cap=10**6):
    a, b = deque(p1), deque(p2)
    start = (tuple(a), tuple(b))
    for t in range(1, cap):
        x, y = a.popleft(), b.popleft()
        if x == y:
            return "tie", t
        if RANK[x] > RANK[y]:
            a.append(x); a.append(y)
        else:
            b.append(y); b.append(x)
        if not a or not b:
            return "ended", t
        if (tuple(a), tuple(b)) == start:
            return "cycle", t
    return "cap", cap


def number_cards(p1, p2, rng=None):
    """Replace letters by distinct integers, all A > all B > ... > all E. Within a letter the order
    is either positional or shuffled (rng), to show the conclusion does not depend on it."""
    slots = [(1, i, c) for i, c in enumerate(p1)] + [(2, i, c) for i, c in enumerate(p2)]
    by_letter = defaultdict(list)
    for s in slots:
        by_letter[s[2]].append(s)
    val = {}
    nxt = 1
    for letter in "EDCBA":
        group = by_letter[letter][:]
        if rng:
            rng.shuffle(group)
        for s in group:
            val[s] = nxt
            nxt += 1
    q1 = [val[(1, i, c)] for i, c in enumerate(p1)]
    q2 = [val[(2, i, c)] for i, c in enumerate(p2)]
    return q1, q2


def card_loop(q1, q2, cap=10**7):
    a, b = deque(q1), deque(q2)
    seen = {}
    t = 0
    while a and b and t < cap:
        key = (tuple(a), tuple(b))
        if key in seen:
            return seen[key], t - seen[key], key
        seen[key] = t
        x, y = a.popleft(), b.popleft()
        if x > y:
            a.append(x); a.append(y)
        else:
            b.append(y); b.append(x)
        t += 1
    return None, None, None


def loop_stats(key, lam):
    a, b = deque(key[0]), deque(key[1])
    winners, lost_to, pairs = [], defaultdict(set), []
    for _ in range(lam):
        x, y = a.popleft(), b.popleft()
        if x > y:
            a.append(x); a.append(y); winners.append(1); lost_to[y].add(x); pairs.append((x, y))
        else:
            b.append(y); b.append(x); winners.append(2); lost_to[x].add(y); pairs.append((y, x))
    assert (tuple(a), tuple(b)) == key
    # circular run lengths
    L = len(winners)
    s = next(i for i in range(L) if winners[i] != winners[i - 1])
    runs, r = [], 1
    for j in range(1, L + 1):
        if j < L and winners[(s + j) % L] == winners[(s + j - 1) % L]:
            r += 1
        else:
            runs.append(r); r = 1
    cards = sorted(set(key[0]) | set(key[1]))
    cat = {c: 0 for c in cards}
    changed = True
    while changed:
        changed = False
        for c in cards:
            if lost_to[c]:
                v = 1 + max(cat[w] for w in lost_to[c])
                if v != cat[c]:
                    cat[c] = v; changed = True
    gaps = defaultdict(int)
    for w, l in pairs:
        gaps[cat[l] - cat[w]] += 1
    return sorted(set(runs)), 1 + max(cat.values()), dict(sorted(gaps.items()))


if __name__ == "__main__":
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    rng = random.Random(7)
    for k in range(1, K + 1):
        n = 8 * k + 6
        p1, p2 = letter_position(k)
        assert len(p1) + len(p2) == n
        status, per = play_letters(p1, p2)
        line = "k=%2d n=%3d  letters: %s after %d (4k+4=%d)" % (k, n, status, per, 4 * k + 4)
        results = []
        for trial in range(3):   # positional numbering, then two shuffled numberings
            q1, q2 = number_cards(p1, p2, rng if trial else None)
            mu, lam, key = card_loop(q1, q2)
            if lam is None:
                results.append("ended or hit the cap"); continue
            runs, ncat, gaps = loop_stats(key, lam)
            thm3 = (runs == [n & -n]) and set(gaps) == {1}
            results.append("L=%d (%s n+2) tail=%d runs=%s cats=%d gaps=%s %s"
                           % (lam, "a multiple of" if lam % (n + 2) == 0 else "not a multiple of", mu, runs, ncat, gaps,
                              "Theorem-3 type" if thm3 else "not Theorem-3 type"))
        print(line)
        for r in results:
            print("        " + r)
