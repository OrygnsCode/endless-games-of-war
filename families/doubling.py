"""Spivey-style doubling of category words.
A category word is a pair of strings over the letters A, B, C, ...; a letter earlier in the alphabet is stronger.
Category-level War: the letter nearer 'A' wins; equal letters meeting = invalid (not a category cycle).
double(): every letter X -> X followed by the next letter (Spivey Thm 3, step 2).
to_cards(): Spivey's Lemma 1, category A gets the top ranks, then B, ...; within a category ranks are assigned
in order of first appearance (any numbering in which every letter beats every later letter gives the same winners)."""
from collections import deque, Counter

def cat_play(p1, p2, cap=100000):
    A, B = deque(p1), deque(p2); seen = {}; t = 0; wins = []
    while A and B and t < cap:
        s = (''.join(A), ''.join(B))
        if s in seen: return 'cycle', t - seen[s], ''.join(wins[seen[s]:])
        seen[s] = t
        a, b = A.popleft(), B.popleft()
        if a == b: return 'tie', None, None
        if a < b: A.extend((a, b)); wins.append('1')
        else: B.extend((b, a)); wins.append('2')
        t += 1
    return 'ends', None, None

def double(p1, p2):
    nx = lambda x: chr(ord(x) + 1)
    return ''.join(x + nx(x) for x in p1), ''.join(x + nx(x) for x in p2)

def to_cards(p1, p2):
    letters = sorted(set(p1 + p2))
    ranks = {}
    n = len(p1) + len(p2); nxt = n
    for L in letters:  # A highest
        for idx, ch in enumerate(p1 + p2):
            if ch == L: ranks[idx] = nxt; nxt -= 1
    seq = [ranks[i] for i in range(n)]
    return seq[:len(p1)], seq[len(p1):]

def card_loop(p1, p2):
    A, B = deque(p1), deque(p2); seen = {}; t = 0; wins = []
    while A and B:
        s = (tuple(A), tuple(B))
        if s in seen: return t - seen[s], ''.join(wins[seen[s]:])
        seen[s] = t
        a, b = A.popleft(), B.popleft()
        if a > b: A.extend((a, b)); wins.append('1')
        else: B.extend((b, a)); wins.append('2')
        t += 1
    return None, None

def runs(w):
    j = next((i for i in range(len(w)) if w[i] != w[i-1]), None)
    if j is None: return [len(w)]
    w = w[j:] + w[:j]; out = []; r = 1
    for i in range(1, len(w)):
        if w[i] == w[i-1]: r += 1
        else: out.append(r); r = 1
    out.append(r); return out

if __name__ == '__main__':
    base = ('AB', 'DABCD')
    print('base', base, cat_play(*base))
    w = base
    for j in range(1, 4):
        w = double(*w)
        n = len(w[0]) + len(w[1])
        st = cat_play(*w)
        c1, c2 = to_cards(*w)
        lam, wins = card_loop(c1, c2)
        print(f'doublings e={j} n={n} category word P1={w[0]} P2={w[1]}  category-level: {st[0]} period {st[1]}')
        if lam:
            rl = sorted(set(runs(wins)))
            print(f'     as cards: P1={c1} P2={c2}  card loop {lam}, winner run lengths {rl}, n & -n = {n & -n}  ->  {"not Theorem-3 type" if rl != [n & -n] else "Theorem-3 type"}')
        else:
            print('     as cards: game ends (no loop)')
