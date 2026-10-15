# Aligned loops of real War (4 suits, ties allowed) under Delahaye and Mathieu's rules: on a tie both cards go on the
# table and the next pair is turned, and the winner takes the table in reverse order, winning card first.
# A deal is a position where both players hold h = n/2 cards. During the next h flips nobody reaches the cards won in
# them, so flip i compares the i-th cards of the two packs. The phase map F sends a deal to the two won piles when
# flip h ends a trick and both piles have h cards; aligned loops are the periodic points of F.
# Checks: (1) the aligned loops listed by Delahaye and Mathieu for 4, 6 and 8 values are stacks of independent
# 8-card atoms; (2) the base atom 4,2,5,5 | 5,3,5,1: its battles are always between two top cards, and its lower
# cards meet only in the pairs wy, wz, xy, xz; (3) the aligned deals of the patterns (2,1,1,4), (1,1,2,4), (2,2,4)
# are exactly the images of base-atom deals when w = x and/or y = z, and (1,2,1,4) has none; (4) with 5 copies of a
# value there is an aligned loop of 12 cards.
#   python atoms.py
from itertools import permutations

def phase(P1, P2):
    h = len(P1); W1, W2, table, tricks = [], [], [], 0
    for i in range(h):
        x, y = P1[i], P2[i]
        if x == y: table += [x, y]; continue
        table += [min(x, y), max(x, y)]
        (W1 if x > y else W2).extend(reversed(table)); table = []; tricks += 1
    if table or len(W1) != h or len(W2) != h: return None, tricks
    return (W1, W2), tricks

def orbit(P1, P2, cap=64):
    s, seen = (list(P1), list(P2)), []
    for _ in range(cap):
        key = (tuple(s[0]), tuple(s[1]))
        if key in seen: return seen if seen.index(key) == 0 else None
        seen.append(key)
        s, _ = phase(*s)
        if s is None: return None
    return None

def aligned_deals(cards):
    h = len(cards) // 2
    return {(p[:h], p[h:]) for p in set(permutations(cards)) if orbit(p[:h], p[h:])}

if __name__ == "__main__":
    print("(1) Delahaye-Mathieu aligned loops, split into blocks of 4 flips")
    for name, a, b in [("4 values", [2, 1, 4, 4, 2, 1, 3, 3], [4, 2, 4, 1, 3, 2, 3, 1]),
                       ("6 values", [4, 2, 5, 5, 4, 2, 6, 6, 3, 2, 2, 1], [5, 4, 5, 1, 6, 4, 6, 1, 3, 1, 3, 3]),
                       ("8 values", [8, 5, 5, 1, 6, 2, 6, 6, 7, 2, 7, 7, 4, 2, 4, 4],
                                    [8, 1, 8, 8, 6, 5, 5, 1, 7, 3, 3, 1, 4, 3, 3, 2])]:
        o = orbit(a, b)
        blocks = [len(orbit(a[u:u + 4], b[u:u + 4]) or []) for u in range(0, len(a), 4)]
        print(f"  {name}: F-period {len(o)}; F-periods of its 4-flip blocks on their own: {blocks}")

    print("(2) base atom 4,2,5,5 | 5,3,5,1")
    o = orbit([4, 2, 5, 5], [5, 3, 5, 1]); ties, lower = set(), set()
    for P1, P2 in o:
        for x, y in zip(P1, P2):
            if x == y: ties.add(x)
            elif max(x, y) < 5: lower.add((min(x, y), max(x, y)))
    print(f"  F-period {len(o)}, phases of {[phase(list(p), list(q))[1] for p, q in o]} tricks, tied values {sorted(ties)}")
    print(f"  lower cards w,x,y,z = 1,2,3,4 meet in the pairs {sorted(lower)}")

    print("(3) merging lower values of the base atom")
    base = aligned_deals([1, 2, 3, 4, 5, 5, 5, 5])
    for name, f, cards in [("(2,1,1,4)", {1: 1, 2: 1, 3: 2, 4: 3, 5: 4}, [1, 1, 2, 3, 4, 4, 4, 4]),
                           ("(1,1,2,4)", {1: 1, 2: 2, 3: 3, 4: 3, 5: 4}, [1, 2, 3, 3, 4, 4, 4, 4]),
                           ("(2,2,4)", {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}, [1, 1, 2, 2, 3, 3, 3, 3]),
                           ("(1,2,1,4)", {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}, [1, 2, 2, 3, 4, 4, 4, 4])]:
        direct = aligned_deals(cards)
        image = {(tuple(f[c] for c in p), tuple(f[c] for c in q)) for p, q in base}
        print(f"  {name}: {len(direct)} aligned deals, all images of base deals: {direct <= image}")
    print(f"  base (1,1,1,1,4): {len(base)} aligned deals")

    print("(4) 5 copies of the value 2")
    o = orbit([2, 1, 3, 2, 3, 1], [4, 3, 3, 2, 2, 2])
    print(f"  2,1,3,2,3,1 | 4,3,3,2,2,2: aligned, F-period {len(o)}")
