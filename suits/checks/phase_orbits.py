"""Phase map F on deals. A phase is positional: flip i is P1[i] vs P2[i]; ties pile up; a decided pair ends the
trick and the winner takes the pile reversed (natural pickup). F is defined when flip h ends a trick and both
players won h cards. For each known aligned state, print the orbit length and the smallest j with F^j = swap."""
def F(p1, p2):
    h = len(p1); w1, w2, pile = [], [], []
    for i in range(h):
        x, y = p1[i], p2[i]
        pile += [min(x, y), max(x, y)]
        if x != y:
            (w1 if x > y else w2).extend(reversed(pile)); pile = []
    if pile or len(w1) != h or len(w2) != h:
        return None
    return tuple(w1), tuple(w2)

STATES = {
    'atom (2,2,4)': ((3, 2, 3, 1), (2, 1, 3, 3)),
    'atom (1,1,1,1,4)': ((5, 3, 5, 1), (4, 2, 5, 5)),
    'atom (1,1,2,4)': ((4, 3, 4, 1), (3, 2, 4, 4)),
    'atom (2,1,1,4) a': ((4, 2, 4, 1), (3, 1, 4, 4)),
    'atom (2,1,1,4) b': ((4, 3, 4, 1), (2, 1, 4, 4)),
    'V4 #1': ((2, 1, 4, 4, 3, 2, 3, 1), (4, 2, 4, 1, 2, 1, 3, 3)),
    'V4 #3': ((4, 1, 4, 4, 3, 1, 3, 3), (4, 2, 2, 1, 3, 2, 2, 1)),
    'V6': ((4, 2, 6, 6, 4, 1, 5, 5, 3, 1, 3, 3), (6, 4, 6, 2, 5, 4, 5, 1, 3, 2, 2, 1)),
}
if __name__ == '__main__':
    for name, s in STATES.items():
        orbit = [s]; swapj = None
        while True:
            t = F(*orbit[-1])
            if t is None: print(name, 'phase map undefined at step', len(orbit)); break
            if swapj is None and t == (s[1], s[0]): swapj = len(orbit)
            if t == s: print('%-18s orbit length %d, F^%s = swap' % (name, len(orbit), swapj)); break
            orbit.append(t)
