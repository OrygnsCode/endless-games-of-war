# The count of war_ref.py in a few lines, in the form used for a program in an OEIS entry; prints a(1)..a(10).
from itertools import permutations
from collections import deque

def a(n):  # deals of cards 1..n for which War (winning card, then losing card, under the winner's pile) never ends
    count = 0
    for deal in permutations(range(1, n + 1)):
        p1, p2, seen = deque(deal[0::2]), deque(deal[1::2]), set()
        while p1 and p2:
            state = (tuple(p1), tuple(p2))
            if state in seen:
                count += 1
                break
            seen.add(state)
            x, y = p1.popleft(), p2.popleft()
            if x > y:
                p1.extend((x, y))
            else:
                p2.extend((y, x))
    return count

print([a(n) for n in range(1, 11)])
