"""Write the two cycle-count tables in ../data from the counting formulas.

  odd_n_cycles.tsv        odd n: the number of cycles (odd_formula.py), with the split by length and the
                          number of canonical positions (player 1's top card is n) on a cycle.
                          For odd n every cycle is of Spivey's Theorem-3 type.
  spivey_type_cycles.tsv  even n: the cycles of Spivey's Theorem-3 type (t3_count.py), with the split
                          by length.

Cycles are counted once per pair {cycle, cycle with the players exchanged}.

  python tables.py              odd n up to 41, even n up to 46
  python tables.py 25 30        smaller limits
"""
import os
import sys
from fractions import Fraction

from odd_formula import D_K
from t3_count import D3

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def split_text(lens):
    return " ".join("%d:%d" % (L, int(v)) for L, v in sorted(lens.items()))


def odd_counts(n):
    """(cycles, canonical positions on a cycle, {length: cycles}) for odd n"""
    if n < 5:
        return 0, 0, {}
    D, K, by = D_K(n)
    lens = {}
    for a, b, L, c in by:
        lens[L] = lens.get(L, 0) + c
    assert sum(lens.values()) == D and all(v.denominator == 1 for v in lens.values())
    return D, K, lens


def even_counts(n):
    """(cycles of Theorem-3 type, {length: cycles}) for even n"""
    M, rows, total = D3(n)
    lens = {}
    for a, b, L, e in rows:
        lens[L] = lens.get(L, 0) + Fraction(M * e, L)
    assert sum(lens.values()) == total and all(v.denominator == 1 for v in lens.values())
    return total, lens


if __name__ == "__main__":
    odd_max = int(sys.argv[1]) if len(sys.argv) > 1 else 41
    even_max = int(sys.argv[2]) if len(sys.argv) > 2 else 46
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "spivey_type_cycles.tsv"), "w", newline="\n") as f:
        f.write("# n\tblock_length_2^v\tcycles_of_theorem_3_type\tcycles_by_length (length:count)\n")
        for n in range(2, even_max + 1, 2):
            total, lens = even_counts(n)
            f.write("%d\t%d\t%d\t%s\n" % (n, n & -n, total, split_text(lens)))
            f.flush()
            print("even n=%d done" % n, flush=True)
    with open(os.path.join(DATA, "odd_n_cycles.tsv"), "w", newline="\n") as f:
        f.write("# n\tcycles\tcanonical_positions_on_a_cycle\tcycles_by_length (length:count)\n")
        for n in range(1, odd_max + 1, 2):
            D, K, lens = odd_counts(n)
            f.write("%d\t%d\t%d\t%s\n" % (n, D, K, split_text(lens)))
            f.flush()
            print("odd n=%d done" % n, flush=True)
