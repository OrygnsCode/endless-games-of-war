"""Spivey's card categories on a War loop. Category 0 = never loses in the loop;
category = 1 + the largest category among the cards that beat it (Spivey p.749). Spivey (2010, Sec. 3)
shows that these are equivalent: the players alternate winning some fixed number of turns in a row;
every loss is to a card one category above; every loss is to a card one or two categories above. So a
loop that does not alternate in fixed runs must contain a loss to a card 3 or more categories above."""
from collections import deque, defaultdict
import sys

def loop_losses(p1, p2, lam):
    a, b = deque(p1), deque(p2); lost_to = defaultdict(set); winners = []
    for _ in range(lam):
        x, y = a.popleft(), b.popleft()
        if x > y: a.append(x); a.append(y); lost_to[y].add(x); winners.append(1)
        else:     b.append(y); b.append(x); lost_to[x].add(y); winners.append(2)
    assert (list(a), list(b)) == (list(p1), list(p2)), "not a loop of that length"
    return lost_to, winners

def categories(cards, lost_to):
    # Spivey p.749: A = never loses; B = loses only to A; C = loses only to A or B; ...
    # so cat(c) = 1 + max(cat of the cards that beat it).
    cat = {c: 0 for c in cards}
    changed = True
    while changed:
        changed = False
        for c in cards:
            if lost_to[c]:
                v = 1 + max(cat[w] for w in lost_to[c])
                if v != cat[c]:
                    cat[c] = v; changed = True
    return cat

for label, p1, p2, lam in [
    ("n=14 loop of 96", [3,5,1,14,9,12,7,8,6], [2,13,10,11,4], 96),
    ("n=14 loop of 96 (the position in the paper)", [1,13,11,9,4], [3,5,2,14,12,10,8,7,6], None),
    ("n=14 loop of 112 (control)", [7,2,14,9,10,3], [13,6,5,1,12,8,11,4], 112),
]:
    if lam is None:   # a start position: find its loop first
        a, b = deque(p1), deque(p2); seen = {}; t = 0
        while True:
            k = (tuple(a), tuple(b))
            if k in seen: lam = t - seen[k]; p1, p2 = list(k[0]), list(k[1]); break
            seen[k] = t; x, y = a.popleft(), b.popleft()
            if x > y: a.append(x); a.append(y)
            else: b.append(y); b.append(x)
            t += 1
    lost_to, w = loop_losses(p1, p2, lam)
    cards = sorted(set(p1) | set(p2)); cat = categories(cards, lost_to)
    gaps = sorted({cat[c] - cat[v] for c in cards for v in lost_to[c]})
    far = [(c, v, cat[c] - cat[v]) for c in cards for v in lost_to[c] if cat[c] - cat[v] >= 3]
    print("%s: loop %d, categories %s" % (label, lam, dict(sorted(cat.items()))))
    print("   category gaps over all losses: %s ; losses to 3+ categories above (%d): %s" % (gaps, len(far), far))
