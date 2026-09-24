"""Look at single War cycles in plain Python.

Samples random canonical positions (player 1's top card is the highest), finds the loop the
game falls into, and prints the loop's length, the winner of each turn, and the lengths
of the runs of consecutive wins by one player.

  python inspect_loops.py 14 96        find loops of length 96 at n = 14
"""
import random
import sys
from collections import deque


def play_round(a, b):
    x, y = a.popleft(), b.popleft()
    if x > y:
        a.append(x); a.append(y)
        return 1
    b.append(y); b.append(x)
    return 2


def find_loop(p1, p2, cap=100000):
    a, b = deque(p1), deque(p2)
    seen = {}
    t = 0
    while a and b and t < cap:
        key = (tuple(a), tuple(b))
        if key in seen:
            return key, t - seen[key]
        seen[key] = t
        play_round(a, b)
        t += 1
    return None, None


def winners_around(key, lam):
    a, b = deque(key[0]), deque(key[1])
    return [play_round(a, b) for _ in range(lam)], (tuple(a), tuple(b)) == key


def runs_circular(w):
    L = len(w)
    s = next(i for i in range(L) if w[i] != w[i - 1])
    out, run = [], 1
    for j in range(1, L + 1):
        if j < L and w[(s + j) % L] == w[(s + j - 1) % L]:
            run += 1
        else:
            out.append((w[(s + j - 1) % L], run))
            run = 1
    return out


if __name__ == "__main__":
    n = int(sys.argv[1])
    want = int(sys.argv[2])
    rng = random.Random(1)
    found = 0
    tries = 0
    while found < 3 and tries < 2_000_000:
        tries += 1
        rest = list(range(n - 1))
        rng.shuffle(rest)
        k = rng.randrange(0, n - 1)
        p1, p2 = [n - 1] + rest[:k], rest[k:]
        key, lam = find_loop(p1, p2)
        if key is None or lam != want:
            continue
        found += 1
        w, back = winners_around(key, lam)
        runs = runs_circular(w)
        print("sample %d after %d tries: start P1=%s P2=%s" % (found, tries, [c + 1 for c in p1], [c + 1 for c in p2]))
        print("  loop length %d, returns to itself: %s, P1 wins %d / P2 wins %d turns"
              % (lam, back, w.count(1), w.count(2)))
        print("  loop state: P1=%s  P2=%s" % ([c + 1 for c in key[0]], [c + 1 for c in key[1]]))
        print("  winner runs around the loop (player, length): %s" % runs)
        print("  distinct run lengths: %s" % sorted(set(r for _, r in runs)))
    print("done, %d tries" % tries)
