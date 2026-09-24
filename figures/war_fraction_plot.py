# Figure: share of the n! deals of cards 1..n that never end (values as in data/b_file.txt).
# Output: war_fraction.svg.
from math import factorial
a = [0, 0, 0, 0, 30, 0, 2304, 0, 218680, 395940, 28223770, 0, 4880546113, 3790165176, 1095264882758, 0]
N = len(a)
W, H = 790, 420
L, R, T, B = 78, 180, 20, 70          # plot margins (series labels go in the right margin)
pw, ph = W - L - R, H - T - B
X = lambda n: L + (n - 0.5) / N * pw
Y = lambda p: T + ph - p / 100 * ph
BLUE, ORANGE = "#2a78d6", "#eb6834"
BLACK, DARKGRAY, GRAY, GRIDGRAY, BACKGROUND = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"
pct = [100 * v / factorial(n) for n, v in enumerate(a, 1)]
odd = [(n, pct[n - 1]) for n in range(1, N + 1) if a[n - 1] and n % 2]
even = [(n, pct[n - 1]) for n in range(1, N + 1) if a[n - 1] and n % 2 == 0]
zero = [n for n in range(1, N + 1) if a[n - 1] == 0]
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
     f'<rect width="{W}" height="{H}" fill="{BACKGROUND}"/>']
for p in range(0, 101, 20):                       # grid lines and y-axis labels
    s.append(f'<line x1="{L}" y1="{Y(p):.1f}" x2="{L+pw}" y2="{Y(p):.1f}" stroke="{GRIDGRAY}" stroke-width="1"/>')
    s.append(f'<text x="{L-10}" y="{Y(p)+4:.1f}" font-size="12" fill="{DARKGRAY}" text-anchor="end">{p}%</text>')
for n in range(1, N + 1):
    s.append(f'<text x="{X(n):.1f}" y="{T+ph+22}" font-size="12" fill="{DARKGRAY}" text-anchor="middle">{n}</text>')
s.append(f'<text x="{L+pw/2:.1f}" y="{H-18}" font-size="13" fill="{DARKGRAY}" text-anchor="middle">n = number of cards</text>')
s.append(f'<text transform="translate(22,{T+ph/2:.1f}) rotate(-90)" font-size="13" fill="{DARKGRAY}" text-anchor="middle">share of deals that never end</text>')
def poly(pts, col):
    d = " ".join(f"{X(n):.1f},{Y(p):.1f}" for n, p in pts)
    s.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="2"/>')
# each parity is joined through its zeros, so no segment passes over a zero
poly([(n, pct[n - 1]) for n in range(1, N + 1, 2)], BLUE)
poly([(n, pct[n - 1]) for n in range(2, N + 1, 2)], ORANGE)
for n, p in odd:
    s.append(f'<circle cx="{X(n):.1f}" cy="{Y(p):.1f}" r="5.5" fill="{BLUE}" stroke="{BACKGROUND}" stroke-width="2"/>')
for n, p in even:
    s.append(f'<rect x="{X(n)-5:.1f}" y="{Y(p)-5:.1f}" width="10" height="10" rx="1.5" fill="{ORANGE}" stroke="{BACKGROUND}" stroke-width="2"/>')
for n in zero:
    s.append(f'<circle cx="{X(n):.1f}" cy="{Y(0):.1f}" r="5" fill="{BACKGROUND}" stroke="{GRAY}" stroke-width="2"/>')
# series labels at the right edge instead of a legend
lx = L + pw + 14
n, p = odd[-1]
s.append(f'<circle cx="{lx}" cy="{Y(p):.1f}" r="5" fill="{BLUE}"/><text x="{lx+10}" y="{Y(p)+4:.1f}" font-size="12.5" fill="{BLACK}">odd n</text>')
n, p = even[-1]
s.append(f'<rect x="{lx-5}" y="{Y(p)-18:.1f}" width="10" height="10" rx="1.5" fill="{ORANGE}"/><text x="{lx+10}" y="{Y(p)-9:.1f}" font-size="12.5" fill="{BLACK}">even n</text>')
s.append(f'<circle cx="{lx}" cy="{Y(0)-2:.1f}" r="5" fill="{BACKGROUND}" stroke="{GRAY}" stroke-width="2"/><text x="{lx+10}" y="{Y(0)+2:.1f}" font-size="12.5" fill="{BLACK}">no endless deal</text>')
s.append(f'<text x="{lx+10}" y="{Y(0)+17:.1f}" font-size="11" fill="{DARKGRAY}">n = 1, 2, 3, 4, 6, 8, 12, 16</text>')
s.append('</svg>')
open("war_fraction.svg", "w", encoding="utf-8").write("\n".join(s))
print("wrote war_fraction.svg")
for n in range(1, N + 1): print(n, a[n-1], f"{pct[n-1]:.3f}%")
