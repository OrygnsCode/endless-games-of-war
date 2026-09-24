"""Shape of War loops from random deals, in plain Python. Random deals of n cards (Spivey's rule,
winner's card then loser's under the winner's pile): find the loop each one falls into, tally the loop
lengths, and print the winner sequence of loops of one chosen length as run lengths.

  python loop_shape.py n loop_length trials [seed]
  python loop_shape.py 17 0 20000 1        (loop_length 0: only the tally)
"""
import random, sys
from collections import deque, Counter

def play(A, B):
    A = deque(A); B = deque(B); seen = {}; t = 0; wins = []
    while A and B:
        key = (tuple(A), tuple(B))
        if key in seen:
            start = seen[key]
            return t - start, wins[start:], key
        seen[key] = t
        a = A.popleft(); b = B.popleft()
        if a > b: A.append(a); A.append(b); wins.append('1')
        else: B.append(b); B.append(a); wins.append('2')
        t += 1
    return None, None, None

def runs(w):
    # cyclic run lengths, starting at a run boundary
    L = len(w)
    j = next(i for i in range(L) if w[i] != w[i - 1])
    w = w[j:] + w[:j]
    out = []; r = 1
    for i in range(1, L):
        if w[i] == w[i - 1]: r += 1
        else: out.append(r); r = 1
    out.append(r)
    return out

n = int(sys.argv[1]); want = int(sys.argv[2]); trials = int(sys.argv[3]); seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
random.seed(seed)
cards = list(range(1, n + 1))
lens = Counter(); shown = 0
for _ in range(trials):
    random.shuffle(cards)
    lam, w, key = play(cards[0::2], cards[1::2])
    if lam is None: continue
    lens[lam] += 1
    if lam == want and shown < 3:
        shown += 1
        rl = runs(w)
        print(f"loop length {lam}: run lengths {rl}  (distinct {sorted(set(rl))})")
        print(f"  a position on the loop: P1={list(key[0])} P2={list(key[1])}")
print('loop lengths seen:', dict(sorted(lens.items())))
