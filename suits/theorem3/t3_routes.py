# Meetings in cycles of Theorem-3 type, predicted from the routes and checked against a full cycle.
# Movement of a card in the forced play: from place i < M of a group to place 2i of a new group of the same player,
# from place i >= M to place 2(i - M) + 1 of a new group of the other player; it waits 2a blocks with player 1 and 2b
# with player 2, one more when i >= M.  A route of R blocks carries R/2 cards, one for each group index of the right
# parity mod R.  Through a meeting type (place i < M of one player, place M + i of the other) two cards on routes of
# lengths R1, R2 meet iff their phases differ by a fixed amount mod gcd(R1, R2), so the pairs fall into
# G = gcd(R1/2, R2/2) classes and each type reaches one class.
# For every shape this compares (1) the number of meeting pairs between each two adjacent levels, predicted this way,
# with the number found by playing a full cycle, and (2) completeness predicted by "G = 1 for every pair of routes on
# adjacent levels" with the actual completeness.
#   python t3_routes.py 52 68          (the listed n)
#   python t3_routes.py all 124        (every n = m * 2^v <= 124 with m >= 5 odd and 1 <= v <= 3)
import sys
from math import gcd
from t3_suits import popc, forced, meetings

def routes(M, a, b):
    nxt = {}
    for p in (0, 1):
        for i in range(2 * M):
            w = (2 * a if p == 0 else 2 * b) + (1 if i >= M else 0)
            nxt[(p, i)] = (((p, 2 * i) if i < M else (1 - p, 2 * (i - M) + 1)), w)
    seen, out = set(), []
    for s0 in nxt:
        if s0 in seen: continue
        s, L, members = s0, 0, []
        while s not in seen:
            seen.add(s); members.append(s); s2, w = nxt[s]; L += w; s = s2
        out.append((popc(s0[1]), L, members))
    return out

def predicted(M, a, b):
    R = routes(M, a, b); w = {0: 2 * a, 1: 2 * b}
    where = {}
    for k, (lev, L, members) in enumerate(R):
        o = 0
        for s in members:
            where[s] = (k, o); o += w[s[0]] + (1 if s[1] >= M else 0)
    classes = {}
    for (p, i), (k1, o1) in where.items():
        if i >= M: continue
        k2, o2 = where[(1 - p, M + i)]
        classes.setdefault((k1, k2), set()).add((o2 + w[1 - p] + 1 - o1 - w[p]) % gcd(R[k1][1], R[k2][1]))
    counts, comp = {}, True
    for (k1, k2), cl in classes.items():
        R1, R2 = R[k1][1], R[k2][1]; G = gcd(R1 // 2, R2 // 2)
        counts[R[k1][0]] = counts.get(R[k1][0], 0) + (R1 // 2) * (R2 // 2) * len(cl) // G
        comp &= G == 1
    return counts, comp

def actual(n, a, v):
    s1, s2 = forced(n, a); letter = s1 + s2
    pairs = meetings(s1, s2)
    counts = {j: sum(1 for w, l in pairs if letter[w] == j) for j in range(v + 1)}
    size = [letter.count(j) for j in range(v + 2)]
    return counts, all(counts[j] == size[j] * size[j + 1] for j in range(v + 1))

def sizes(arg):
    if arg[0] == "all":
        top = int(arg[1])
        return [m << v for v in (1, 2, 3) for m in range(5, top + 1, 2) if m << v <= top]
    return [int(x) for x in arg]

if __name__ == "__main__":
    shapes = complete = wrong_count = wrong_comp = 0
    for n in sizes(sys.argv[1:]):
        v = (n & -n).bit_length() - 1; M, m = 2 ** v, n >> v; h = (m - 1) // 2
        row = []
        for a in range(1, h):
            pc, pcomp = predicted(M, a, h - a); ac, acomp = actual(n, a, v)
            shapes += 1; complete += acomp; wrong_count += pc != ac; wrong_comp += pcomp != acomp
            row.append(f"{a}:{'C' if acomp else '-'}{'' if pc == ac and pcomp == acomp else '!'}")
        print(f"n={n} m={m} v={v}: " + " ".join(row), flush=True)
    print(f"{shapes} shapes, {complete} complete; predicted meeting counts wrong in {wrong_count}, "
          f"predicted completeness wrong in {wrong_comp}")
