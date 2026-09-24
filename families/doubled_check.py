"""Check of the doubled family, n = 2^j (8k+6), at the letter level and, for small n, with numbered cards.

Letters are integers, 0 = A (strongest). D(w) = interleave(w, w+1). For j >= 0, k >= 1:
  T = D^j(ABBC), Y = D^j(CDDE), Z = D^j(DE), L = 4*2^j
  start: P1 = T^k, P2 = Z T^k Y, n = 2^j (8k+6).
Checks at the letter level: no tie ever, returns to the start, period, winner-run lengths.
Then, for a few small n, the real numbered-card game: never ends, loop length, winner runs.

  python doubled_check.py
"""
from collections import deque

A, B, C, Dd, E = 0, 1, 2, 3, 4


def dbl(w):
    out = []
    for x in w:
        out += [x, x + 1]
    return out


def dj(w, j):
    for _ in range(j):
        w = dbl(w)
    return w


def runs_circular(winners):
    L = len(winners)
    s = next((i for i in range(L) if winners[i] != winners[i - 1]), None)
    if s is None:
        return {L}
    out, r = set(), 1
    for t in range(1, L + 1):
        if t < L and winners[(s + t) % L] == winners[(s + t - 1) % L]:
            r += 1
        else:
            out.add(r); r = 1
    return out


def letter_play(p1, p2, cap):
    a, b = deque(p1), deque(p2)
    start = (tuple(a), tuple(b))
    winners = []
    for t in range(1, cap + 1):
        x, y = a.popleft(), b.popleft()
        if x == y:
            return "tie at turn %d" % t, None
        if x < y:            # smaller index = stronger letter
            a.append(x); a.append(y); winners.append(1)
        else:
            b.append(y); b.append(x); winners.append(2)
        if not a or not b:
            return "ended at turn %d" % t, None
        if (tuple(a), tuple(b)) == start:
            return "cycle, period %d" % t, winners
    return "no return within %d" % cap, None


def card_play(p1, p2, cap=3_000_000):
    # number cards: letter with larger index gets smaller numbers; within a letter by position
    slots = [(1, i, c) for i, c in enumerate(p1)] + [(2, i, c) for i, c in enumerate(p2)]
    slots.sort(key=lambda s: (-s[2], s[0], s[1]))
    val = {s: v for v, s in enumerate(slots, start=1)}
    a = deque(val[(1, i, c)] for i, c in enumerate(p1))
    b = deque(val[(2, i, c)] for i, c in enumerate(p2))
    start = (tuple(a), tuple(b))
    winners = []
    for t in range(1, cap + 1):
        x, y = a.popleft(), b.popleft()
        if x > y:
            a.append(x); a.append(y); winners.append(1)
        else:
            b.append(y); b.append(x); winners.append(2)
        if not a or not b:
            return "ended", None
        if (tuple(a), tuple(b)) == start:
            return t, winners
    return "no return within cap", None


if __name__ == "__main__":
    fails = 0
    for j in range(0, 6):
        for k in range(1, 7):
            T = dj([A, B, B, C], j); Z = dj([Dd, E], j); Y = dj([C, Dd, Dd, E], j)
            L = 4 * 2 ** j
            p1 = T * k
            p2 = Z + T * k + Y
            n = len(p1) + len(p2)
            assert n == 2 ** j * (8 * k + 6)
            status, w = letter_play(p1, p2, cap=10 * (k + 2) * L)
            expect = (k + 1) * L
            runs = runs_circular(w) if w else None
            good = w is not None and status == "cycle, period %d" % expect and runs == {1, 2 ** (j + 1)}
            fails += not good
            print("j=%d k=%d n=%4d  %-24s expected period %5d  runs %-10s %s"
                  % (j, k, n, status, expect, sorted(runs) if runs else "-", "OK" if good else "FAIL"))
    print("letter-level failures:", fails)
    print("--- real cards (small n) ---")
    for j, k in [(0, 1), (1, 1), (0, 2), (1, 2), (2, 1)]:
        T = dj([A, B, B, C], j); Z = dj([Dd, E], j); Y = dj([C, Dd, Dd, E], j)
        p1 = T * k; p2 = Z + T * k + Y
        lam, w = card_play(p1, p2)
        print("j=%d k=%d n=%3d  card loop length %s  runs %s" % (j, k, len(p1) + len(p2), lam,
              sorted(runs_circular(w)) if w else "-"))
