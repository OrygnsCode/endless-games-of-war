"""Exact number of cycles of single-suit War for odd n from the slot poset; no games are played.

Poset for parameters (a, b), nb = a + b + 1, g1 = gcd(a, nb), g2 = gcd(b, nb) (coprime):
  B cards fall into g1*g2 cells (j mod g1, j mod g2), each with m = nb/(g1 g2) cards;
  player 1's A cards form g1 groups of a/g1, group r above every B in row r;
  player 2's A cards form g2 groups of b/g2, group c above every B in column c.
e(a, b) = number of linear extensions. Elements of one cell/group are interchangeable, so we count sequences of
class labels (bottom-up) and multiply by the factorials of the class sizes.
  D(n)   = number of cycles up to exchanging the players = sum_a e(a, b) / lcm(n+1, 2a, 2b)
  K(n)   = number of canonical positions (player 1's top card is n) that lie on a cycle
         = sum_a e'(a, b), e' = extensions of the poset without A_0 (A_0 is maximal, so fixing it = card n
           leaves exactly the linear extensions of the rest)
"""
import math
import sys
from functools import lru_cache
from fractions import Fraction


def e_ab(a, b, drop=False):
    nb = a + b + 1
    g1, g2 = math.gcd(a, nb), math.gcd(b, nb)
    m, s1, s2 = nb // (g1 * g2), a // g1, b // g2
    rowcap = tuple(s1 - (1 if (drop and r == 0) else 0) for r in range(g1))
    # bottom-up. State: tuple of B counts per cell (row-major), plus counts of A cards placed per row group / column group.
    # A cards never block anything, so only B counts matter for the constraints; A counts are tracked by totals per group.
    @lru_cache(maxsize=None)
    def f(cells, arow, acol):
        # cells: tuple of g1*g2 counts; arow: tuple of g1 counts; acol: tuple of g2 counts
        if all(c == m for c in cells) and arow == rowcap and all(x == s2 for x in acol):
            return 1
        t = 0
        for k in range(g1 * g2):
            if cells[k] < m:
                t += f(cells[:k] + (cells[k] + 1,) + cells[k + 1:], arow, acol)
        for r in range(g1):
            if arow[r] < rowcap[r] and all(cells[r * g2 + c] == m for c in range(g2)):
                t += f(cells, arow[:r] + (arow[r] + 1,) + arow[r + 1:], acol)
        for c in range(g2):
            if acol[c] < s2 and all(cells[r * g2 + c] == m for r in range(g1)):
                t += f(cells, arow, acol[:c] + (acol[c] + 1,) + acol[c + 1:])
        return t
    seqs = f((0,) * (g1 * g2), (0,) * g1, (0,) * g2)
    fa = 1
    for x in rowcap:
        fa *= math.factorial(x)
    return seqs * math.factorial(m) ** (g1 * g2) * fa * math.factorial(s2) ** g2


def D_K(n):
    h = (n - 1) // 2
    D = Fraction(0); K = Fraction(0); by = []
    for a in range(1, h):
        b = h - a
        e = e_ab(a, b)
        L = math.lcm(n + 1, 2 * a, 2 * b)
        D += Fraction(e, L); K += e_ab(a, b, drop=True)
        by.append((a, b, L, Fraction(e, L)))
    assert D.denominator == 1 and K.denominator == 1
    return int(D), int(K), by


if __name__ == "__main__":
    # python odd_formula.py N [NMIN] [--split]: odd n from NMIN (default 5) to N; --split also prints, for each
    # split (a, b), the positions on cycles e(a, b), the canonical positions on cycles e'(a, b) and the cycle length
    nums = [x for x in sys.argv[1:] if not x.startswith("--")]
    N = int(nums[0]) if nums else 31
    NMIN = int(nums[1]) if len(nums) > 1 else 5
    for n in range(NMIN + (NMIN % 2 == 0), N + 1, 2):
        D, K, by = D_K(n)
        lens = {}
        for a, b, L, c in by:
            lens[L] = lens.get(L, 0) + c
        # D already counts each cycle once up to swap (sum over ordered (a, b) of e/(L/2), halved)
        split = {L: int(v) for L, v in sorted(lens.items())}
        print("n=%2d  D=%d  K=%d  lengths(up to swap)=%s" % (n, D, K, split), flush=True)
        if "--split" in sys.argv:
            for a, b, L, c in by:
                print("   (a,b)=(%d,%d)  length %d  e=%d  canonical positions on cycles e'=%d"
                      % (a, b, L, e_ab(a, b), e_ab(a, b, drop=True)), flush=True)
