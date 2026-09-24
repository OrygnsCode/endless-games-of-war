"""Plain reference simulator for single-suit War, written directly from the rule.

Rule (Spivey 2010): cards 1..n are dealt into two face-down piles (player 1 gets ceil(n/2),
player 2 floor(n/2)). Each turn both players turn over their top card; the higher card wins,
and the winner puts the winning card on the bottom of their own pile, then the losing card below
it. A player with no cards loses. a(n) counts deck orders (n! of them, deck position 0,2,4,...
to player 1, 1,3,5,... to player 2) for which the game never ends.

Every fixed bijection from deck orders to pile pairs gives the same count, so the dealing
convention does not affect a(n).

  python war_ref.py 10
"""
import itertools
import sys
from collections import deque


def cycles(p1, p2):
    a, b = deque(p1), deque(p2)
    seen = set()
    while a and b:
        key = (tuple(a), tuple(b))
        if key in seen:
            return True
        seen.add(key)
        x, y = a.popleft(), b.popleft()
        if x > y:
            a.append(x)
            a.append(y)
        else:
            b.append(y)
            b.append(x)
    return False


def count(n):
    total = 0
    for deck in itertools.permutations(range(1, n + 1)):
        if cycles(deck[0::2], deck[1::2]):
            total += 1
    return total


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    for n in range(1, N + 1):
        print("n=%d  a(n)=%d" % (n, count(n)), flush=True)
