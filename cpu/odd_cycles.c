/* Distinct War cycles up to swapping players, odd n. A second method, independent of the
   canonical scans: it uses the structure theorems instead of simulating every canonical position.
   - Every cycle, up to swap, passes a position where player 1's top card is n (card n never loses).
   - Spivey Thm 6 (odd n): in a cycle the players alternate winning every turn, and a player about to
     win holds an even number of cards. Card n wins, so at a canonical position on a cycle player 1
     holds 2a cards and player 2 holds 2b+1, a, b >= 1, and turn t (0-based) is won by player 1 when t
     is even and by player 2 when t is odd.
   - For the first min(2a, 2b+1) turns both players play cards from the starting piles (the cards
     they win go behind them), so P1[t] > P2[t] for even t and P2[t] > P1[t] for odd t. We
     enumerate by depth-first search under these constraints only.
   - Each complete position is then played for lambda = lcm(n+1, 2a, 2b) turns (the exact cycle length
     for this a, b, proved in the paper); it is on a cycle iff it is back at the start with every turn
     alternating. Early exit on a non-alternating turn or an empty pile.
   - Each cycle class {C, swap(C)} is counted once, at its minimal canonical key (as distinct_cycles.c).
   Usage: odd_cycles n threads [a]      Build: gcc -O3 -march=native -fopenmp -o odd_cycles odd_cycles.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>

#define CAP 64
typedef struct { uint8_t c[2][CAP]; uint8_t h[2], len[2]; } St;
static inline void push(St *s, int p, int v) { s->c[p][(s->h[p] + s->len[p]) & (CAP - 1)] = (uint8_t)v; s->len[p]++; }
static inline int step(St *s) {
    int a = s->c[0][s->h[0]], b = s->c[1][s->h[1]];
    s->h[0] = (s->h[0] + 1) & (CAP - 1); s->len[0]--;
    s->h[1] = (s->h[1] + 1) & (CAP - 1); s->len[1]--;
    if (a > b) { push(s, 0, a); push(s, 0, b); return 0; }
    push(s, 1, b); push(s, 1, a); return 1;
}
static int eq(const St *x, const St *y) {
    for (int p = 0; p < 2; p++) {
        if (x->len[p] != y->len[p]) return 0;
        for (int i = 0; i < x->len[p]; i++)
            if (x->c[p][(x->h[p] + i) & (CAP - 1)] != y->c[p][(y->h[p] + i) & (CAP - 1)]) return 0;
    }
    return 1;
}
/* lexicographic key: player 1's length, then player 1's cards, then player 2's (top first) */
static int keycmp(const St *x, int xs, const St *y, int ys) {   /* xs/ys: 1 = read with players swapped */
    int xl0 = x->len[xs], yl0 = y->len[ys];
    if (xl0 != yl0) return xl0 < yl0 ? -1 : 1;
    for (int q = 0; q < 2; q++) {
        int px = xs ^ q, py = ys ^ q;
        for (int i = 0; i < x->len[px]; i++) {
            int u = x->c[px][(x->h[px] + i) & (CAP - 1)], v = y->c[py][(y->h[py] + i) & (CAP - 1)];
            if (u != v) return u < v ? -1 : 1;
        }
    }
    return 0;
}
static long long gcdll(long long a, long long b) { while (b) { long long t = a % b; a = b; b = t; } return a; }
static long long lcmll(long long a, long long b) { return a / gcdll(a, b) * b; }

static int n, A2, B2;               /* n, 2a, 2b+1 */
static long long lam;

typedef struct { long long distinct, oncycle, leaves; } Cnt;

static void finish(int *p1, int *p2, Cnt *cnt) {
    cnt->leaves++;
    St s; memset(&s, 0, sizeof s);
    for (int i = 0; i < A2; i++) push(&s, 0, p1[i]);
    for (int i = 0; i < B2; i++) push(&s, 1, p2[i]);
    St t = s;
    for (long long k = 0; k < lam; k++) {
        int w = step(&t);
        if (w != (int)(k & 1)) return;                 /* must alternate: P1 wins even turns */
        if (t.len[0] == 0 || t.len[1] == 0) return;
    }
    if (!eq(&t, &s)) return;
    cnt->oncycle++;
    /* minimal canonical key over the cycle and its swapped twin */
    St best = s; int bests = 0; St u = s;
    for (long long k = 0; k < lam; k++) {
        if (u.c[0][u.h[0]] == n && keycmp(&u, 0, &best, bests) < 0) { best = u; bests = 0; }
        if (u.c[1][u.h[1]] == n && keycmp(&u, 1, &best, bests) < 0) { best = u; bests = 1; }
        step(&u);
    }
    if (keycmp(&s, 0, &best, bests) == 0) cnt->distinct++;
}
/* fill slots in turn order: slot index 2t = P1[t], 2t+1 = P2[t] (if they exist) */
static void dfs(int t, int side, int *p1, int *p2, uint32_t used, Cnt *cnt) {
    int maxt = A2 > B2 ? A2 : B2;
    if (t == maxt) { finish(p1, p2, cnt); return; }
    int exists = side == 0 ? (t < A2) : (t < B2);
    if (!exists) { if (side == 0) dfs(t, 1, p1, p2, used, cnt); else dfs(t + 1, 0, p1, p2, used, cnt); return; }
    for (int v = 1; v <= n; v++) {
        if (used >> v & 1) continue;
        if (side == 1 && t < A2) {                      /* both players have a card at turn t: constraint */
            if ((t & 1) == 0 && !(p1[t] > v)) continue; /* P1 wins even turns */
            if ((t & 1) == 1 && !(v > p1[t])) continue; /* P2 wins odd turns */
        }
        if (side == 0) { p1[t] = v; dfs(t, 1, p1, p2, used | (1u << v), cnt); }
        else           { p2[t] = v; dfs(t + 1, 0, p1, p2, used | (1u << v), cnt); }
    }
}
int main(int argc, char **argv) {
    n = atoi(argv[1]); int th = atoi(argv[2]); int only_a = argc > 3 ? atoi(argv[3]) : 0;
    if (n % 2 == 0 || n > 31) { fprintf(stderr, "odd n <= 31 only\n"); return 1; }
    omp_set_num_threads(th);
    long long total = 0, totcyc = 0, totleaves = 0;
    for (int a = 1; 2 * a <= n - 3; a++) {
        int b = (n - 1) / 2 - a; if (b < 1) continue;
        if (only_a && a != only_a) continue;
        A2 = 2 * a; B2 = 2 * b + 1; lam = lcmll(lcmll(n + 1, 2 * a), 2 * b);
        long long dsum = 0, csum = 0, lsum = 0;
        /* parallelize over the first two free choices: P2[0] (< n, since P1[0] = n wins) and P1[1] */
        #pragma omp parallel for collapse(2) schedule(dynamic, 1) reduction(+:dsum,csum,lsum)
        for (int v0 = 1; v0 < n; v0++)
            for (int v1 = 1; v1 < n; v1++) {
                if (v1 == v0) continue;
                int p1[CAP], p2[CAP]; Cnt cnt = {0, 0, 0};
                p1[0] = n; p2[0] = v0; p1[1] = v1;
                uint32_t used = (1u << n) | (1u << v0) | (1u << v1);
                dfs(1, 1, p1, p2, used, &cnt);          /* next slot: P2[1] */
                dsum += cnt.distinct; csum += cnt.oncycle; lsum += cnt.leaves;
            }
        printf("  a=%d b=%d (P1 %d, P2 %d cards, cycle length %lld): positions tried %lld, on a cycle %lld, distinct cycles %lld\n",
               a, b, A2, B2, lam, lsum, csum, dsum);
        fflush(stdout);
        total += dsum; totcyc += csum; totleaves += lsum;
    }
    printf("n=%d: DISTINCT cycles up to swap %lld (canonical positions on cycles %lld; positions tried %lld)\n", n, total, totcyc, totleaves);
    return 0;
}
