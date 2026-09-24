# Check of the deal-reachability argument for the doubled family.
# Build the numbered start (every letter beats every later letter), play 2^(j+1) turns (end of P1's
# first run), undo 2^j player-2 wins, and check: the result is a balanced deal, it is not on the loop
# (pile sizes), and replaying 2^j turns forward lands exactly on the loop state.
from collections import Counter
def D(w): return [x for c in w for x in (c, c + 1)]
def Dj(w, j):
    for _ in range(j): w = D(w)
    return w
def cstep(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return ((p1[1:] + (a, b), p2[1:]) if a > b else (p1[1:], p2[1:] + (b, a)))
def undo_p2(s):
    p1, p2 = s; w, l = p2[-2], p2[-1]
    assert w > l, "tail is not winner-then-loser"
    return ((l,) + p1, (w,) + p2[:-2])
ok = True
for j in range(0, 5):
    for k in range(1, 5):
        T = Dj([0,1,1,2], j); Z = Dj([3,4], j); Y = Dj([2,3,3,4], j); L = len(T)
        lstart = (T * k, Z + T * k + Y); n = len(lstart[0]) + len(lstart[1])
        cnt = Counter(lstart[0] + lstart[1]); it = {}; v = n
        for letter in sorted(cnt): it[letter] = iter(range(v, v - cnt[letter], -1)); v -= cnt[letter]
        s = (tuple(next(it[x]) for x in lstart[0]), tuple(next(it[x]) for x in lstart[1]))
        for _ in range(2 ** (j + 1)): s = cstep(s)
        loop_state = s
        d = s
        for _ in range(2 ** j): d = undo_p2(d)
        balanced = len(d[0]) == len(d[1]) == n // 2
        # loop pile sizes for P1: [kL, kL + 2^(j+1)]; a deal needs n/2 = kL + 3*2^j
        off_loop = not (k * L <= len(d[0]) <= k * L + 2 ** (j + 1))
        f = d
        for _ in range(2 ** j): f = cstep(f)
        good = balanced and off_loop and f == loop_state
        ok &= good
        print(f"j={j} k={k} n={n:4d}: deal balanced={balanced}, off-loop={off_loop}, replays onto loop in 2^j={2**j} turns: {f == loop_state}")
print("all cases pass:", ok)
