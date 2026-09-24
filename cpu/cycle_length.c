/* Plays one War position (winning card, then losing card, under the winner's pile) and reports whether
   the game ends or cycles. For a cycle it prints the cycle length (Brent's method), the number of turns
   before the game enters the cycle, and whether n + 2^v divides the length, where 2^v = n & -n.
   The position is given either as two piles of card values, top card first, separated by commas:
       cycle_length 1,13,11,9,4 3,5,2,14,12,10,8,7,6
   or as the start of the doubled family with parameters j >= 0 and k >= 1:
       cycle_length doubled j k
   which builds T = D^j(ABBC), Z = D^j(DE), Y = D^j(CDDE), where D replaces each letter x by x followed by
   the next letter; player 1 gets T^k and player 2 gets Z T^k Y. The cards are numbered so that every
   letter beats every later letter: A cards get the highest values, and within a letter the values
   decrease in order of appearance, player 1's pile first.
   An optional last argument caps the number of turns (default 10^12). At most 255 cards.
   Build: gcc -O3 -march=native -o cycle_length cycle_length.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define CAP 256
typedef struct { uint8_t c[2][CAP]; int h[2], len[2]; } St;

static inline int step(St *s) {
    int a = s->c[0][s->h[0]], b = s->c[1][s->h[1]];
    s->h[0] = (s->h[0] + 1) & (CAP - 1); s->len[0]--;
    s->h[1] = (s->h[1] + 1) & (CAP - 1); s->len[1]--;
    int w = a > b ? 0 : 1, hi = a > b ? a : b, lo = a > b ? b : a;
    s->c[w][(s->h[w] + s->len[w]) & (CAP - 1)] = (uint8_t)hi; s->len[w]++;
    s->c[w][(s->h[w] + s->len[w]) & (CAP - 1)] = (uint8_t)lo; s->len[w]++;
    return s->len[0] == 0 || s->len[1] == 0;
}
static int eq(const St *x, const St *y) {
    for (int p = 0; p < 2; p++) {
        if (x->len[p] != y->len[p]) return 0;
        for (int i = 0; i < x->len[p]; i++)
            if (x->c[p][(x->h[p] + i) & (CAP - 1)] != y->c[p][(y->h[p] + i) & (CAP - 1)]) return 0;
    }
    return 1;
}
static int parse_pile(const char *arg, int *out) {
    int m = 0; const char *p = arg;
    while (*p) {
        char *e; long v = strtol(p, &e, 10);
        if (e == p || v < 1 || v > 255 || m >= CAP - 1) return -1;
        out[m++] = (int)v; p = e;
        if (*p == ',') p++; else if (*p) return -1;
    }
    return m;
}
static int apply_d(const int *w, int m, int *out) {           /* D: x -> x, x+1 */
    for (int i = 0; i < m; i++) { out[2 * i] = w[i]; out[2 * i + 1] = w[i] + 1; }
    return 2 * m;
}
static int dj(const int *w, int m, int j, int *out) {
    int a[CAP], b[CAP];
    memcpy(a, w, m * sizeof(int));
    for (int t = 0; t < j; t++) {
        if (2 * m > CAP) return -1;
        m = apply_d(a, m, b); memcpy(a, b, m * sizeof(int));
    }
    memcpy(out, a, m * sizeof(int));
    return m;
}
static int build_doubled(int j, int k, int *p1, int *m1, int *p2, int *m2) {
    const int T0[] = {0, 1, 1, 2}, Z0[] = {3, 4}, Y0[] = {2, 3, 3, 4};
    int T[CAP], Z[CAP], Y[CAP];
    int lt = dj(T0, 4, j, T), lz = dj(Z0, 2, j, Z), ly = dj(Y0, 4, j, Y);
    if (lt < 0 || lz < 0 || ly < 0 || k < 1) return -1;
    int n = k * lt + lz + k * lt + ly;
    if (n > 255) return -1;
    int L1[CAP], L2[CAP], a = 0, b = 0;
    for (int r = 0; r < k; r++) for (int i = 0; i < lt; i++) L1[a++] = T[i];
    for (int i = 0; i < lz; i++) L2[b++] = Z[i];
    for (int r = 0; r < k; r++) for (int i = 0; i < lt; i++) L2[b++] = T[i];
    for (int i = 0; i < ly; i++) L2[b++] = Y[i];
    int cnt[64] = {0}, next[64];
    for (int i = 0; i < a; i++) cnt[L1[i]]++;
    for (int i = 0; i < b; i++) cnt[L2[i]]++;
    int v = n;
    for (int x = 0; x < 64; x++) { next[x] = v; v -= cnt[x]; }  /* letter 0 is the strongest */
    for (int i = 0; i < a; i++) p1[i] = next[L1[i]]--;
    for (int i = 0; i < b; i++) p2[i] = next[L2[i]]--;
    *m1 = a; *m2 = b;
    return n;
}

int main(int argc, char **argv) {
    int p1[CAP], p2[CAP], m1, m2, argi;
    if (argc >= 4 && strcmp(argv[1], "doubled") == 0) {
        int j = atoi(argv[2]), k = atoi(argv[3]);
        if (j < 0 || build_doubled(j, k, p1, &m1, p2, &m2) < 0) { fprintf(stderr, "doubled j k: need j >= 0, k >= 1 and at most 255 cards\n"); return 1; }
        printf("doubled family j=%d k=%d\n", j, k);
        argi = 4;
    } else if (argc >= 3) {
        m1 = parse_pile(argv[1], p1); m2 = parse_pile(argv[2], p2);
        if (m1 < 1 || m2 < 1) { fprintf(stderr, "each pile: comma-separated card values 1..255, top card first\n"); return 1; }
        argi = 3;
    } else {
        fprintf(stderr, "usage: cycle_length P1 P2 [cap]   or   cycle_length doubled j k [cap]\n");
        return 1;
    }
    long long cap = argc > argi ? atoll(argv[argi]) : 1000000000000LL;
    int n = m1 + m2, seen[256] = {0};
    if (n > 255) { fprintf(stderr, "at most 255 cards\n"); return 1; }
    for (int i = 0; i < m1; i++) seen[p1[i]]++;
    for (int i = 0; i < m2; i++) seen[p2[i]]++;
    for (int x = 1; x <= n; x++) if (seen[x] != 1) { fprintf(stderr, "the cards must be 1..%d, each once\n", n); return 1; }

    St s0; memset(&s0, 0, sizeof s0);
    for (int i = 0; i < m1; i++) s0.c[0][i] = (uint8_t)p1[i];
    for (int i = 0; i < m2; i++) s0.c[1][i] = (uint8_t)p2[i];
    s0.len[0] = m1; s0.len[1] = m2;
    printf("n=%d: player 1 holds %d cards, player 2 holds %d\n", n, m1, m2);

    /* Brent: find the cycle length lam */
    St s = s0, saved = s0; long long power = 1, lam = 0, t = 0;
    while (1) {
        if (step(&s)) { printf("the game ends after %lld turns\n", t + 1); return 0; }
        t++; lam++;
        if (eq(&s, &saved)) break;
        if (lam == power) { saved = s; power <<= 1; lam = 0; }
        if (t >= cap) { printf("not settled within %lld turns\n", cap); return 0; }
    }
    /* turns before the cycle: advance one copy lam turns, then both together until they meet */
    St x = s0, y = s0; long long mu = 0;
    for (long long i = 0; i < lam; i++) step(&y);
    while (!eq(&x, &y)) { step(&x); step(&y); mu++; }
    int v = n & -n;
    printf("the game cycles: cycle length %lld, entered after %lld turns\n", lam, mu);
    if (lam % (n + v) == 0) printf("n + 2^v = %d divides the length: %lld = %d x %lld\n", n + v, lam, n + v, lam / (n + v));
    else printf("n + 2^v = %d does NOT divide the length\n", n + v);
    return 0;
}
