# The 44-card loop found by Clement Courbet (11 values in 4 suits), as listed with the code of Delahaye and Mathieu.
# Plays it under their rules (a tie puts both cards on the table and the next pair is turned; the winner takes the
# table in reverse order, winning card first) and checks: the length of the cycle, that no two equal values meet on
# the cycle (so the rule for battles does not matter there), that the players alternate runs of exactly 4 wins
# (Theorem-3 type for 44 = 11 * 4), the sizes of Spivey's categories, and the shape (a, b): at the start of a block
# of player 1, player 1 holds a groups of 8 cards.
#   python courbet44.py
P1 = [1, 3, 4, 9, 4, 9, 6, 5, 10, 7, 6, 10, 5, 7, 10, 11, 11, 2, 8, 7, 9, 5]
P2 = [8, 1, 4, 1, 4, 8, 2, 11, 6, 3, 7, 2, 8, 3, 9, 1, 2, 3, 10, 5, 6, 11]
cards = [(v, i) for i, v in enumerate(P1 + P2)]          # (value, identity): the four copies stay distinct
s = (tuple(cards[:22]), tuple(cards[22:]))

def trick(s):
    # one trick; returns the new position and the number of ties in it
    A, B, table, ties = list(s[0]), list(s[1]), [], 0
    while A and B:
        a, b = A.pop(0), B.pop(0)
        if a[0] == b[0]: table += [a, b]; ties += 1; continue
        table += [b, a] if a[0] > b[0] else [a, b]
        (A if a[0] > b[0] else B).extend(reversed(table))
        return (tuple(A), tuple(B)), ties
    return None, ties

seen, t, ties_before = {}, 0, 0
while s not in seen:
    seen[s] = t; s, k = trick(s); t += 1; ties_before += k
loop, ties_on = [s], 0
u, k = trick(s); ties_on += k
while u != s:
    loop.append(u); u, k = trick(u); ties_on += k
print(f"enters its cycle after {seen[s]} tricks ({ties_before} ties on the way); cycle of {len(loop)} tricks, "
      f"{ties_on} ties on the cycle")

wins = [1 if x[0][0][0] > x[1][0][0] else 2 for x in loop]
c = next(i for i in range(len(wins)) if wins[i] != wins[i - 1]); w = wins[c:] + wins[:c]
runs, r = set(), 1
for i in range(1, len(w)):
    if w[i] == w[i - 1]: r += 1
    else: runs.add(r); r = 1
runs.add(r)
print(f"run lengths of wins: {sorted(runs)}")

beaten = {}
for x in loop:
    a, b = x[0][0], x[1][0]
    win, lose = (a, b) if a[0] > b[0] else (b, a)
    beaten.setdefault(lose, set()).add(win)
cat = {}
def category(c):
    if c not in cat: cat[c] = 0 if c not in beaten else 1 + max(category(d) for d in beaten[c])
    return cat[c]
sizes = [sum(1 for c in cards if category(c) == j) for j in range(max(map(category, cards)) + 1)]
print(f"category sizes: {sizes}")

i = next(k for k in range(len(loop)) if wins[k] == 1 and wins[k - 1] == 2)
print(f"at the start of a block of player 1: player 1 holds {len(loop[i][0])} cards, so a = {len(loop[i][0]) // 8}")
