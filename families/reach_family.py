"""Deal-reachability for the whole doubled family. For j, k: build the start position
(T^k, Z T^k Y) in numbered cards (Spivey's Lemma 1 numbering), play 2^(j+1) turns (player 1's winning run in
phase 1), then undo 2^j player-2 wins using the (winner, loser) pairs at the end of player 2's pile
(which is Y = D^(j+1)(CD) there). Check: every undo is legal, the result is a deal (n/2 cards each),
playing forward from it reaches the loop state, and, for n <= 60, the numbered loop is not of Theorem-3 type
(larger loops rest on the letter-level check)."""
from collections import deque
from doubled_phases import Dj
from doubling import to_cards, card_loop, runs
def fwd(p1, p2, t):
    A, B = deque(p1), deque(p2)
    for _ in range(t):
        a, b = A.popleft(), B.popleft()
        if a > b: A.extend((a, b))
        else: B.extend((b, a))
    return list(A), list(B)
bad = 0; cnt = 0
for j in range(0, 6):
    T, Y, Z = Dj('ABBC', j), Dj('CDDE', j), Dj('DE', j)
    for k in range(1, 6):
        w1, w2 = T * k, Z + T * k + Y
        c1, c2 = to_cards(w1, w2); n = len(c1) + len(c2)
        s1, s2 = fwd(c1, c2, 2 ** (j + 1))          # on the loop, player 1 at its maximum size
        p1, p2 = list(s1), list(s2); ok = True
        for _ in range(2 ** j):                    # undo player-2 wins
            if not (len(p2) >= 2 and p2[-2] > p2[-1]): ok = False; break
            x, y = p2[-2], p2[-1]
            p2 = [x] + p2[:-2]; p1 = [y] + p1
        ok &= len(p1) == len(p2) == n // 2
        ok &= fwd(p1, p2, 2 ** j) == (s1, s2)       # the deal reaches the loop state
        if n <= 60:   # full numbered loop only for small n (large loops are millions of turns)
            lam, wins = card_loop(p1, p2)
            rl = sorted(set(runs(wins))) if lam else None
            ok &= rl == [1, 2 ** (j + 1)]
        else:
            lam, rl = 'not played (the letter-level check covers it)', 'n/a'
        cnt += 1; bad += (not ok)
        print(f'j={j} k={k} n={n}: deal {len(p1)}+{len(p2)}, enters loop after {2**j} turns, loop {lam}, runs {rl} {"OK" if ok else "FAIL"}', flush=True)
print(f'{cnt} cases, {bad} failures')
