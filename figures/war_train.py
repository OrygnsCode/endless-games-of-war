# Figure: the 8k+6 family at the category level (k = 3, n = 30). Checkpoints of the letter game:
# start, S(0), S(1), S(2), start again. The defect (ADBE in player 1's pile, CDDE and DE in player 2's pile)
# is outlined; the rest of each pile is copies of ABBC. Category shade: A darkest ... E lightest.
RANK = {c: i for i, c in enumerate("EDCBA")}
def lstep(s):
    p1, p2 = s; a, b = p1[0], p2[0]
    return ((p1[1:] + a + b, p2[1:]) if RANK[a] > RANK[b] else (p1[1:], p2[1:] + b + a))
k = 3
start = ("ABBC" * k, "DE" + "ABBC" * k + "CDDE")
checkpoints = [0, 2, 6, 10, 4 * k + 4]
states = {}; s = start
for t in range(4 * k + 5):
    states[t] = s; s = lstep(s)
SHADE = {"A": "#0d366b", "B": "#1c5cab", "C": "#3987e5", "D": "#86b6ef", "E": "#cde2fb"}
TXT = {"A": "#ffffff", "B": "#ffffff", "C": "#ffffff", "D": "#0b0b0b", "E": "#0b0b0b"}
ORANGE, BLACK, DARKGRAY, BACKGROUND = "#eb6834", "#0b0b0b", "#52514e", "#fcfcfb"
cw, ch, gap = 20, 24, 2
x1, x2 = 190, 190 + 16 * (cw + gap) + 30
W = x2 + 20 * (cw + gap) + 20
rowh = 2 * ch + 26
H = 36 + len(checkpoints) * rowh + 50
labels = {0: "start", 2: "after 2 turns", 6: "after 6 turns", 10: "after 10 turns", 4 * k + 4: f"after {4*k+4} turns: start again"}
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
       f'<rect width="{W}" height="{H}" fill="{BACKGROUND}"/>',
       f'<text x="{x1}" y="28" font-size="12.5" font-weight="bold" fill="{BLACK}">player 1 (top card on the left)</text>',
       f'<text x="{x2}" y="28" font-size="12.5" font-weight="bold" fill="{BLACK}">player 2</text>']
def pile(x0, y0, word, marks):
    for i, c in enumerate(word):
        x = x0 + i * (cw + gap)
        out.append(f'<rect x="{x}" y="{y0}" width="{cw}" height="{ch}" rx="3" fill="{SHADE[c]}"/>')
        out.append(f'<text x="{x + cw/2}" y="{y0 + ch/2 + 4.5}" font-size="12.5" font-weight="bold" fill="{TXT[c]}" text-anchor="middle">{c}</text>')
    for (a, b) in marks:
        x = x0 + a * (cw + gap) - 2; w = (b - a) * (cw + gap) + 2
        out.append(f'<rect x="{x}" y="{y0 - 2}" width="{w}" height="{ch + 4}" rx="4" fill="none" stroke="{ORANGE}" stroke-width="2.5"/>')
def find_marks(word, pats):
    m = []
    for p in pats:
        i = word.find(p)
        while i >= 0:
            m.append((i, i + len(p))); i = word.find(p, i + 1)
    return m
y = 42
for t in checkpoints:
    p1, p2 = states[t]
    out.append(f'<text x="20" y="{y + ch/2 + 4 + (ch + 6)/2}" font-size="12.5" fill="{BLACK}">{labels[t]}</text>')
    pile(x1, y + (ch + 6) // 2, p1, find_marks(p1, ["ADBE"]))
    m2 = find_marks(p2, ["CDDE"])
    if p2.startswith("DE"): m2.append((0, 2))
    pile(x2, y + (ch + 6) // 2, p2, m2)
    y += rowh
# legend
lx = 20; ly = H - 26
for i, c in enumerate("ABCDE"):
    out.append(f'<rect x="{lx + i*34}" y="{ly - 14}" width="{cw}" height="{ch - 4}" rx="3" fill="{SHADE[c]}"/><text x="{lx + i*34 + cw/2}" y="{ly + 1}" font-size="11.5" font-weight="bold" fill="{TXT[c]}" text-anchor="middle">{c}</text>')
out.append(f'<text x="{lx + 5*34 + 6}" y="{ly + 1}" font-size="12" fill="{DARKGRAY}">category, strongest to weakest</text>')
out.append(f'<rect x="{lx + 400}" y="{ly - 15}" width="44" height="22" rx="4" fill="none" stroke="{ORANGE}" stroke-width="2.5"/><text x="{lx + 452}" y="{ly + 1}" font-size="12" fill="{DARKGRAY}">defect</text>')
out.append('</svg>')
open("war_train30.svg", "w", encoding="utf-8").write("\n".join(out))
print("wrote war_train30.svg", W, H)
