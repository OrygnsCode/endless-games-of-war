# Spivey's 52-card deal (Integers 10 (2010), p. 752), in category letters A (strongest) to D:
#   player 1: CDABBCBCCDABBCBCCDABBCBCCD    player 2: BCBCCDABBCBCCDABBCBCCDABBC
# It lies on a letter cycle with no tie.  Following the cards by their starting places gives the numbered cycle and
# every pair of cards that meet on it.  Each A meets each B, each B each C and each C each D, so with suits every
# category would have to consist of whole ranks, and 6, 19, 20, 7 are not multiples of 4 (or of 2).
#   python spivey52.py
from math import lcm
from t3_suits import meetings

P1 = "CDABBCBCCDABBCBCCDABBCBCCD"
P2 = "BCBCCDABBCBCCDABBCBCCDABBC"
s1, s2 = ["ABCD".index(c) for c in P1], ["ABCD".index(c) for c in P2]
letter = s1 + s2; n = len(letter)

p1, p2, P = list(s1), list(s2), 0                       # letter period
while True:
    a, b = p1.pop(0), p2.pop(0)
    (p1 if a < b else p2).extend((a, b) if a < b else (b, a)); P += 1
    if p1 == s1 and p2 == s2: break

q1 = [(x, q) for q, x in enumerate(s1)]; q2 = [(x, len(s1) + q) for q, x in enumerate(s2)]
for _ in range(P):                                      # place permutation after one letter period
    a, b = q1.pop(0), q2.pop(0)
    if a[0] < b[0]: q1 += [a, b]
    else: q2 += [b, a]
start = {q: (0, q) for q in range(len(s1))} | {len(s1) + q: (1, q) for q in range(len(s2))}
at = {v: q for q, v in start.items()}
now = {q: (0, d) for d, (_, q) in enumerate(q1)} | {q: (1, d) for d, (_, q) in enumerate(q2)}
pi = {q: at[now[q]] for q in range(n)}
lens, seen = [], set()
for q0 in range(n):
    if q0 in seen: continue
    q, k = q0, 0
    while True:
        seen.add(q); q = pi[q]; k += 1
        if q == q0: break
    lens.append(k)

pairs = meetings(s1, s2)
size = [letter.count(j) for j in range(4)]
print(f"letter period {P}, numbered cycle {P * lcm(*lens)} turns")
print(f"category sizes A..D: {size}")
for j in range(3):
    met = sum(1 for w, l in pairs if letter[w] == j and letter[l] == j + 1)
    print(f"  {'ABCD'[j]} beats {'ABCD'[j + 1]}: {met} of {size[j] * size[j + 1]} pairs meet")
print("other pairs that meet:", sum(1 for w, l in pairs if letter[l] != letter[w] + 1))
