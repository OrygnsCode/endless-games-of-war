"""Check of the phase identities for the doubled family (see the paper).
Letters: A best; x+1 = next letter. D(w) = interleave(w, w+1) (Spivey's doubling). For j >= 0, k >= 1:
  T = D^j(ABBC), L = |T| = 4*2^j, H = D^j(AB), Q = D^j(BC), Y = D^j(CDDE), Z = D^j(DE),
  X = interleave(H, H+3)
  start: P1 = T^k, P2 = Z T^k Y        (n = 2^j (8k+6) cards)
Claims, each checked by letter-level simulation with no ties:
  phase 1 (L turns):      start          -> (T^(k-1) X,              Q T^(k-1) Y T)
  step i (L turns):       (T^(k-1-i) X T^i, Q T^(k-1-i) Y T^(i+1)) -> same with i+1   (0 <= i <= k-2)
  final (L turns):        (X T^(k-1), Q Y T^k) -> start
after(i) below is the position after (i+1) L turns.
So the category cycle has period L(k+1); winner runs are 2^(j+1) (phases 1, middle) and 1 (final)."""
from collections import deque
nx = lambda w, s=1: ''.join(chr(ord(c) + s) for c in w)
def D(w): return ''.join(c + nx(c) for c in w)
def Dj(w, j):
    for _ in range(j): w = D(w)
    return w
def inter(a, b): return ''.join(x + y for x, y in zip(a, b))
def play(p1, p2, turns):
    A, B = deque(p1), deque(p2); win = []
    for _ in range(turns):
        a, b = A.popleft(), B.popleft()
        if a == b: raise ValueError('tie')
        if a < b: A.extend((a, b)); win.append('1')
        else: B.extend((b, a)); win.append('2')
    return ''.join(A), ''.join(B), ''.join(win)
if __name__ == "__main__":
    bad = 0; checked = 0
    for j in range(0, 7):
        T, H, Q, Y, Z = Dj('ABBC', j), Dj('AB', j), Dj('BC', j), Dj('CDDE', j), Dj('DE', j)
        X = inter(H, nx(H, 3)); L = len(T)
        for k in range(1, 9):
            start = (T * k, Z + T * k + Y)
            after = lambda i: (T * (k - 1 - i) + X + T * i, Q + T * (k - 1 - i) + Y + T * (i + 1))
            ok = True
            p1, p2, w = play(*start, L); ok &= (p1, p2) == after(0); words = [w]
            for i in range(k - 1):
                p1, p2, w = play(*after(i), L); ok &= (p1, p2) == after(i + 1); words.append(w)
            p1, p2, w = play(*after(k - 1), L); ok &= (p1, p2) == start; words.append(w)
            wf = ''.join(words)
            # full-period check from the start, and run structure
            q1, q2, w2 = play(*start, L * (k + 1)); ok &= (q1, q2) == start and w2 == wf
            runs = set()
            r = 1; ww = wf + wf
            j0 = next(i for i in range(1, len(wf) + 1) if ww[i] != ww[i - 1])
            cyc = ww[j0:j0 + len(wf)]
            for i in range(1, len(cyc)):
                if cyc[i] == cyc[i - 1]: r += 1
                else: runs.add(r); r = 1
            runs.add(r)
            n = len(start[0]) + len(start[1])
            ok &= runs == {1, 2 ** (j + 1)} and n == 2 ** j * (8 * k + 6)
            checked += 1; bad += (not ok)
            if not ok: print('FAIL', j, k, runs)
    print(f'checked {checked} (j=0..6, k=1..8) families: {bad} failures')
