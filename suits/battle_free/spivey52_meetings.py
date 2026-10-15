"""Spivey (2010) p.751-752: a 52-card cycle under winner-first with ties broken by suit.
Category deal, top card first:
  Player 1: CDABBCBCCDABBCBCCDABBCBCCD
  Player 2: BCBCCDABBCBCCDABBCBCCDABBC
A = aces + K of spades and hearts; B = other kings, queens, jacks, tens, nines, 8 of spades;
C = other eights, sevens, sixes, fives, fours, 3 of spades; D = other threes and the twos.
Within a letter, any numbering keeps the cycle (equal letters never meet). We take Spivey's suit order
spade > heart > diamond > club and fill the slots of each letter in decreasing card order, player 1 first.
Then we play strictly (rank, suit) and record every meeting of two cards of the same RANK: in real War
each such meeting would be a battle."""
from collections import deque, Counter

P1 = "CDABBCBCCDABBCBCCDABBCBCCD"
P2 = "BCBCCDABBCBCCDABBCBCCDABBC"
SUITS = "SHDC"                       # spade > heart > diamond > club
RANKS = list(range(14, 1, -1))       # A=14 ... 2
cards = sorted(((r, 3 - SUITS.index(s)) for r in RANKS for s in SUITS), reverse=True)  # strict order, high first


def in_A(c): return c[0] == 14 or (c[0] == 13 and c[1] >= 2)
def in_B(c): return (c[0] == 13 and c[1] < 2) or 9 <= c[0] <= 12 or (c[0] == 8 and c[1] == 3)
def in_C(c): return (c[0] == 8 and c[1] < 3) or 4 <= c[0] <= 7 or (c[0] == 3 and c[1] == 3)
def in_D(c): return (c[0] == 3 and c[1] < 3) or c[0] == 2


groups = {'A': [c for c in cards if in_A(c)], 'B': [c for c in cards if in_B(c)],
          'C': [c for c in cards if in_C(c)], 'D': [c for c in cards if in_D(c)]}
print('category sizes:', {k: len(v) for k, v in groups.items()}, ' letters in deal:', Counter(P1 + P2))
it = {k: iter(v) for k, v in groups.items()}
p1 = deque(next(it[x]) for x in P1)
p2 = deque(next(it[x]) for x in P2)
start = (tuple(p1), tuple(p2))
same_rank = Counter()
for t in range(1, 10 ** 6):
    x, y = p1.popleft(), p2.popleft()
    if x[0] == y[0]:
        same_rank[x[0]] += 1
    if x > y:
        p1.extend((x, y))
    else:
        p2.extend((y, x))
    if not p1 or not p2:
        print('ENDS at turn', t); break
    if (tuple(p1), tuple(p2)) == start:
        print('cycle length', t, '(Spivey: 31,920)')
        break
print('same-rank meetings in one cycle (would be battles in real War):', dict(same_rank), 'total', sum(same_rank.values()))

# which card pairs ever meet over one full cycle (card identity = (rank, suit))
p1 = deque(start[0]); p2 = deque(start[1]); met = set()
cat = {c: k for k, v in groups.items() for c in v}
for t in range(31920):
    x, y = p1.popleft(), p2.popleft()
    met.add(frozenset((x, y)))
    (p1.extend((x, y)) if x > y else p2.extend((y, x)))
for a_, b_ in (('A', 'B'), ('B', 'C'), ('C', 'D'), ('A', 'C'), ('B', 'D'), ('A', 'D')):
    n = sum(1 for u in groups[a_] for w in groups[b_] if frozenset((u, w)) in met)
    print('%s-%s pairs that meet: %d of %d' % (a_, b_, n, len(groups[a_]) * len(groups[b_])))
