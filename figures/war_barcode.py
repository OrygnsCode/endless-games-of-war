# Figure: who wins each turn, once around each of two 14-card cycles. Top: a cycle of Theorem-3 type
# (runs of 2 wins, 112 turns). Bottom: a cycle not of Theorem-3 type (runs of 1 and 2 wins, 96 turns).
def step(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return ((p1[1:] + (a, b), p2[1:]) if a > b else (p1[1:], p2[1:] + (b, a)))
def cycle(start):
    out = [start]; s = step(start)
    while s != start: out.append(s); s = step(s)
    return out
A = ((13, 11, 10, 4), (8, 2, 12, 7, 5, 1, 14, 9, 6, 3))      # on a cycle of 112 turns
B = ((1, 13, 11, 9, 4), (3, 5, 2, 14, 12, 10, 8, 7, 6))      # on a cycle of 96 turns (the position in the paper)
rows = [("Of Theorem-3 type: runs of 2 wins", cycle(A)),
        ("Not of Theorem-3 type: runs of 1 and 2 wins", cycle(B))]
BLUE, ORANGE = "#2a78d6", "#eb6834"
BLACK, BACKGROUND = "#0b0b0b", "#fcfcfb"
cw, gap, bh = 6, 1, 34
W = 60 + 112 * (cw + gap) + 40
H = 200
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
     f'<rect width="{W}" height="{H}" fill="{BACKGROUND}"/>']
y = 30
for title, lp in rows:
    s.append(f'<text x="30" y="{y-10}" font-size="13" fill="{BLACK}">{title} ({len(lp)} turns)</text>')
    for i, st in enumerate(lp):
        col = BLUE if st[0][0] > st[1][0] else ORANGE
        s.append(f'<rect x="{30 + i*(cw+gap)}" y="{y}" width="{cw}" height="{bh}" fill="{col}"/>')
    y += bh + 50
s.append(f'<rect x="30" y="{H-30}" width="12" height="12" fill="{BLUE}"/><text x="48" y="{H-20}" font-size="12.5" fill="{BLACK}">player 1 wins the turn</text>')
s.append(f'<rect x="230" y="{H-30}" width="12" height="12" fill="{ORANGE}"/><text x="248" y="{H-20}" font-size="12.5" fill="{BLACK}">player 2 wins the turn</text>')
s.append('</svg>')
open("war_barcode14.svg", "w", encoding="utf-8").write("\n".join(s))
print("rows:", [len(r[1]) for r in rows])
