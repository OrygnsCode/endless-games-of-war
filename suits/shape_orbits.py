# Test: aligned loops of War with suits, searched by the shapes of their phases (independent of shapes.cpp).
# A phase plays both hands through once, card i of player 1 against card i of player 2. Its shape is the list of
# its tricks, each a run of ties followed by one decided flip, and in an aligned loop each player wins half the
# cards. Once the shape is fixed the phase only moves cards between slots, so a sequence of K shapes is a loop
# exactly when the slots can be labelled with values that agree with every tie (equal), every decided flip (the
# winner is higher) and the return to the start after K phases, using at most CAP copies of any value.
# Equalities go into a union-find, the order is checked for cycles after every phase.
# The winner takes the pile in reverse order of play, as in bataille.py of Delahaye and Mathieu.
# Usage: python shape_orbits.py N K [CAP]    N cards, K phases, CAP copies per value (default 4, 0 = no limit)
import sys, time

def shapes(h):
    # every phase of h flips in which each player wins h/2 flips' worth of cards
    out = []
    def rec(rem, f1, cur):
        if rem == 0:
            if f1 == h // 2: out.append(tuple(cur))
            return
        for t in range(rem):
            f = t + 1
            for w in (1, 2):
                if w == 1 and f1 + f > h // 2: continue
                if w == 2 and rem - f < h // 2 - f1: continue
                cur.append((t, w)); rec(rem - f, f1 + (f if w == 1 else 0), cur); cur.pop()
    rec(h, 0, [])
    return out

def phase(shape, h):
    # slots 0..h-1 are player 1's hand, h..2h-1 player 2's, top first; returns the new slot order,
    # the tied pairs and the decided pairs (winner, loser), all in current slot numbers
    p1, p2 = list(range(h)), list(range(h, 2 * h))
    w1, w2, eq, gt, i = [], [], [], [], 0
    for t, w in shape:
        pile = []
        for _ in range(t):
            eq.append((p1[i], p2[i])); pile += [p1[i], p2[i]]; i += 1
        x, y = p1[i], p2[i]; i += 1
        if w == 1: gt.append((x, y)); pile += [y, x]
        else:      gt.append((y, x)); pile += [x, y]
        (w1 if w == 1 else w2).extend(reversed(pile))
    return w1 + w2, eq, gt

def find(par, a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a

def acyclic(par, strict):
    adj, indeg = {}, {}
    for x, y in strict:
        a, b = find(par, x), find(par, y)
        if a == b: return False
        adj.setdefault(a, set()).add(b); indeg.setdefault(a, 0); indeg.setdefault(b, 0)
    for a in adj:
        for b in adj[a]: indeg[b] += 1
    stack, seen = [v for v, d in indeg.items() if d == 0], 0
    while stack:
        v = stack.pop(); seen += 1
        for u in adj.get(v, ()):
            indeg[u] -= 1
            if indeg[u] == 0: stack.append(u)
    return seen == len(indeg)

def search(N, K, cap):
    h = N // 2
    S = shapes(h)
    moves = [phase(s, h) for s in S]
    nodes, hits, path = [0] * (K + 1), [], []
    def dfs(depth, inv, par, strict):
        # inv[slot] = the starting slot of the card now in slot
        nodes[depth] += 1
        if depth == K:
            par = par[:]
            for j in range(N):
                a, b = find(par, inv[j]), find(par, j)
                if a != b: par[a] = b
            if not acyclic(par, strict): return
            size = {}
            for a in range(N):
                r = find(par, a); size[r] = size.get(r, 0) + 1
            if cap and max(size.values()) > cap: return
            hits.append((tuple(path), sorted(size.values(), reverse=True)))
            return
        for si, (order, eq, gt) in enumerate(moves):
            p = par[:]
            for x, y in eq:
                a, b = find(p, inv[x]), find(p, inv[y])
                if a != b: p[a] = b
            st = strict + [(inv[x], inv[y]) for x, y in gt]
            if not acyclic(p, st): continue
            path.append(si)
            dfs(depth + 1, [inv[o] for o in order], p, st)
            path.pop()
    t0 = time.time()
    dfs(0, list(range(N)), list(range(N)), [])
    print(f'N={N} K={K} cap={cap}: {len(S)} phase shapes, nodes per depth {nodes}, '
          f'realisable shape sequences {len(hits)}, {time.time() - t0:.0f} s')
    for sizes in sorted({tuple(s) for _, s in hits}, reverse=True):
        print('  value class sizes', list(sizes))

if __name__ == '__main__':
    N, K = int(sys.argv[1]), int(sys.argv[2])
    search(N, K, int(sys.argv[3]) if len(sys.argv) > 3 else 4)
