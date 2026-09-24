"""Route rule for the length of a Theorem-3-type cycle, checked against the forced play.
A card at position i (0 <= i < 2M, a (v+1)-bit number) in a group of player X moves to position rot(i) (i -> 2i mod
2M-1, with 2M-1 fixed). If i < M it wins its next turn and stays with X, which takes 2x blocks (x = a for player 1,
b for player 2); if i >= M it loses, which takes 2x+1 blocks, and moves to the other player. A block is M turns.
L = M * lcm over all (position, player) of the route length in blocks."""
import math
from t3_count import forced_play


def route_L(a, b, M):
    def rot(i):
        return 2 * i if i < M else 2 * (i - M) + 1
    Ls = []
    for i0 in range(2 * M):
        for p0 in (0, 1):
            i, p, cost = i0, p0, 0
            while True:
                x = a if p == 0 else b
                if i < M:
                    cost += 2 * x
                else:
                    cost += 2 * x + 1; p ^= 1
                i = rot(i)
                if i == i0 and p == p0:
                    break
            Ls.append(cost)
    return M * math.lcm(*Ls), sorted(set(Ls))


bad = 0
for v in range(0, 4):
    M = 1 << v
    for m in range(5, 64, 2):
        h = (m - 1) // 2
        n = m * M
        if n > 64:
            continue
        lengths = set()
        for a in range(1, h):
            b = h - a
            L1 = forced_play(a, b, M)[0]
            L2, routes = route_L(a, b, M)
            ok = L1 == L2 and L1 % (n + M) == 0
            bad += not ok
            lengths.add(L1)
            if not ok or (a == 1 and m in (5, 9)):
                print("n=%d M=%d (a,b)=(%d,%d) forced L=%d route L=%d routes(blocks)=%s  %s" %
                      (n, M, a, b, L1, L2, routes, "OK" if ok else "MISMATCH"))
        print("n=%d M=%d: the lengths L_{a,b} are %s" % (n, M, sorted(lengths)))
print("mismatches:", bad)
