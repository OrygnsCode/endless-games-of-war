# Classifies the doubled loops not of Theorem-3 type listed by base_enum (the "NEW e m P1 P2" lines, from canon mode
# or from full mode with "list") by
# quantities that do not depend on how the cards are numbered: n, the letter period P, the length P * ord(sigma) of
# the numbered cycle, and the sizes of Spivey's categories. sigma is the permutation of places after one letter
# period; a card stays on its sigma-orbit, so categories are computed on orbits: orbit O' beats orbit O when in some
# turn of one period a place of O' beats a place of O, and the category is 0 if never beaten, else 1 + the largest
# category among the orbits that beat it. Nothing plays a whole numbered cycle.
# usage: python classify_doubled.py e m files...      (e = number of doublings, m = base size)
import sys
from collections import deque, Counter
from math import lcm
D = lambda w: ''.join(c + chr(ord(c) + 1) for c in w)


def to_loop(w1, w2, cap=5_000_000):
    A, B = deque(w1), deque(w2); seen = {}; states = []
    for t in range(cap):
        s = (''.join(A), ''.join(B))
        if s in seen: return states[seen[s]:]
        seen[s] = t; states.append(s)
        a, b = A.popleft(), B.popleft()
        if a == b: return None
        if a < b: A.extend((a, b))
        else: B.extend((b, a))
        if not A or not B: return None
    return None


def invariants(w1, w2, P):
    n1, n = len(w1), len(w1) + len(w2); letter = w1 + w2
    A, B = deque(range(n1)), deque(range(n1, n)); beats = []
    for t in range(P):
        a, b = A.popleft(), B.popleft()
        if letter[a] < letter[b]: A.extend((a, b)); beats.append((a, b))
        else: B.extend((b, a)); beats.append((b, a))
    end = {x: i for i, x in enumerate(list(A) + list(B))}; sigma = [end[q] for q in range(n)]
    orb = [-1] * n; sizes = []; order = 1
    for q in range(n):
        if orb[q] >= 0: continue
        o = [q]; orb[q] = len(sizes); x = sigma[q]
        while x != q: o.append(x); orb[x] = len(sizes); x = sigma[x]
        sizes.append(len(o)); order = lcm(order, len(o))
    beaten_by = {}
    for w, l in beats: beaten_by.setdefault(orb[l], set()).add(orb[w])
    cat = {}
    def c(o):
        if o not in cat: cat[o] = 0 if o not in beaten_by else 1 + max(c(x) for x in beaten_by[o])
        return cat[o]
    per_cat = Counter()
    for o in range(len(sizes)): per_cat[c(o)] += sizes[o]
    return P * order, tuple(per_cat[i] for i in range(max(per_cat) + 1))


def main():
    e, m = int(sys.argv[1]), int(sys.argv[2])
    classes = {}
    for f in sys.argv[3:]:
        for line in open(f):
            if not line.startswith('NEW'): continue
            _, ee, mm, p1, p2 = line.split()
            if int(ee) != e or int(mm) != m: continue
            d1, d2 = p1, p2
            for _ in range(e): d1, d2 = D(d1), D(d2)
            states = to_loop(d1, d2)
            if states is None: continue
            length, sizes = invariants(*states[0], len(states))
            key = (length, sizes)
            classes.setdefault(key, []).append((p1, p2, len(states)))
    print(f'e={e} m={m} n={m << e}: {len(classes)} classes by (numbered length, category sizes A..)')
    for (length, sizes), lst in sorted(classes.items()):
        print(f'  length {length}, categories {len(sizes)} sizes {sizes}, letter periods {sorted(set(x[2] for x in lst))}, '
              f'{len(lst)} base positions, e.g. base {lst[0][0]} | {lst[0][1]}')


if __name__ == '__main__':
    main()
