"""A short, separate implementation of real War under the rules of Delahaye and Mathieu (rangement naturel), used
by the checks in this directory as a second engine next to battles.cpp.

Each trick both players turn over their top card; the pair goes on the table lower card first (on a tie, player 1's
card first). Equal cards: both stay and the next cards are turned. Unequal: the winner takes the table in reverse
order, winning card first. If a hand runs out during a battle the table goes to nobody. The game ends when a hand
is empty at the start of a trick (both empty: a draw), and it cycles when the pair of hands at the start of a trick
repeats."""


def trick(a, b):
    """play one trick on lists a, b (top card first); returns the number of pairs turned over"""
    pile, f = [], 0
    while a and b:
        x, y = a.pop(0), b.pop(0); f += 1
        pile += [y, x] if x > y else [x, y]
        if x != y:
            (a if x > y else b).extend(reversed(pile))
            return f
    return f


def play_to_cycle(p1, p2, limit=10 ** 7):
    """None if the game ends, else the cycle: the list of positions (hand 1, hand 2) at the start of each trick"""
    a, b = list(p1), list(p2)
    seen, order = {}, []
    while a and b and len(order) < limit:
        s = (tuple(a), tuple(b))
        if s in seen:
            return order[seen[s]:]
        seen[s] = len(order); order.append(s)
        trick(a, b)
    return None


def aligned(state, lam):
    """for a position on a cycle of lam tricks: (phase length in tricks if the cycle is aligned else None, battles per lap)"""
    a, b = list(state[0]), list(state[1]); H = (len(a) + len(b)) // 2
    F, eq, bat = [0], [len(a) == len(b)], 0
    for t in range(2 * lam):
        f = trick(a, b)
        if t < lam and f > 1: bat += 1
        F.append(F[-1] + f); eq.append(len(a) == len(b))
    assert (tuple(a), tuple(b)) == state, 'not back after two laps'
    at = {v: i for i, v in enumerate(F)}
    if F[lam] % H: return None, bat
    for t0 in range(lam):
        if eq[t0] and all(F[t0] + j * H in at and eq[at[F[t0] + j * H]] for j in range(1, F[lam] // H + 1)):
            return at[F[t0] + H] - t0, bat
    return None, bat
