/* Base search: odd letter "bases" whose Spivey doubling is a non-Theorem-3 cycle.
   Letters 0..L-1 (0 = A strongest). A position (P1, P2) with |P1|+|P2| = m is a base if the letter game
   from it returns to it (so it lies on a cycle) with no tie (equal letters meeting) and no empty pile.
   Its doubling D(P1), D(P2) (D(w) = interleave(w, w+1)) is then played; we record whether it is again
   a tie-free loop (the doubled game is played until it enters one), and whether the winner runs of
   that loop all have length exactly 2^d, d = doublings (Theorem-3 shape) or not (new type).
   Output: counts of base positions, of doubled positions that enter a tie-free loop, and of doubled positions
   whose loop is not of Theorem-3 type (the field NEW-type), each also weighted by 1/loop-length (for the
   base positions, which lie on their cycles, this is the number of distinct cycles).
   Usage: base_search m letters threads [doublings]      Build: gcc -O3 -march=native -fopenmp -o base_search base_search.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>

#define CAP 128
typedef struct { uint8_t c[2][CAP]; uint8_t h[2], len[2]; } St;
static inline void push(St *s, int p, int v) { s->c[p][(s->h[p] + s->len[p]) & (CAP - 1)] = (uint8_t)v; s->len[p]++; }
/* returns winner 0/1, or -1 on tie */
static inline int step(St *s) {
    int a = s->c[0][s->h[0]], b = s->c[1][s->h[1]];
    if (a == b) return -1;
    s->h[0] = (s->h[0] + 1) & (CAP - 1); s->len[0]--;
    s->h[1] = (s->h[1] + 1) & (CAP - 1); s->len[1]--;
    if (a < b) { push(s, 0, a); push(s, 0, b); return 0; }   /* smaller letter = stronger */
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
/* play from s0; return period if it comes back to s0 with no tie / empty pile within maxsteps, else 0.
   If allruns != NULL, also report whether all winner runs (cyclic) have length exactly runlen. */
static long cycle_through(const St *s0, long maxsteps, int runlen, int *allruns) {
    St s = *s0; int wins[4096]; long t = 0;
    while (t < maxsteps) {
        int w = step(&s);
        if (w < 0) return 0;
        if (s.len[0] == 0 || s.len[1] == 0) return 0;
        if (t < 4096) wins[t] = w;
        t++;
        if (eq(&s, s0)) break;
    }
    if (t >= maxsteps) return 0;
    if (allruns) {
        if (t > 4096) { *allruns = -1; return t; }
        int k = -1;
        for (long i = 0; i < t; i++) if (wins[i] != wins[(i + t - 1) % t]) { k = (int)i; break; }
        if (k < 0) { *allruns = 0; return t; }
        int ok = 1, run = 0, prev = wins[k];
        for (long i = 0; i < t; i++) {
            int w = wins[(k + i) % t];
            if (w == prev) run++; else { if (run != runlen) ok = 0; prev = w; run = 1; }
        }
        if (run != runlen) ok = 0;
        *allruns = ok;
    }
    return t;
}

/* play from s0 until tie / empty pile (return 0) or a loop is found (Brent). Walk the loop once and
   set *allruns = 1 if every cyclic winner run has length runlen, 0 if not. Returns loop length. */
static long enters_loop(const St *s0, long maxsteps, int runlen, int *allruns) {
    St s = *s0, saved = *s0; long power = 1, lam = 0, t = 0;
    while (1) {
        int w = step(&s); if (w < 0) return 0;
        if (s.len[0] == 0 || s.len[1] == 0) return 0;
        t++; lam++;
        if (eq(&s, &saved)) break;
        if (lam == power) { saved = s; power <<= 1; lam = 0; }
        if (t > maxsteps) return 0;
    }
    /* s is on the loop (length lam). Walk to a change of winner, then count runs over exactly lam turns. */
    St u = s; int prev = -1, w0 = -1;
    for (long i = 0; i < lam; i++) { int w = step(&u); if (w < 0) return 0; if (i > 0 && w != prev) { w0 = w; break; } prev = w; }
    if (w0 < 0) { *allruns = 0; return lam; }
    int ok = 1, run = 1, cur = w0;
    for (long i = 1; i < lam; i++) {
        int w = step(&u); if (w < 0) return 0;
        if (w == cur) run++; else { if (run != runlen) ok = 0; cur = w; run = 1; }
    }
    if (run != runlen) ok = 0;
    *allruns = ok;
    return lam;
}
int main(int argc, char **argv) {
    int m = atoi(argv[1]), L = atoi(argv[2]), th = atoi(argv[3]); int ed = argc > 4 ? atoi(argv[4]) : 1; int runlen = 1 << ed;
    long long words = 1; for (int i = 0; i < m; i++) words *= L;
    long maxb = 64L * m * m, maxd = 256L * m * m;
    long long nbase = 0, ndbl = 0, nnew = 0, nunk = 0;
    double cbase = 0, cdbl = 0, cnew = 0;
    long long ex_w = -1; int ex_s = 0;
    omp_set_num_threads(th);
    #pragma omp parallel for schedule(dynamic, 4096) reduction(+:nbase,ndbl,nnew,nunk,cbase,cdbl,cnew)
    for (long long wi = 0; wi < words; wi++) {
        int w[CAP]; long long x = wi;
        for (int i = 0; i < m; i++) { w[i] = (int)(x % L); x /= L; }
        for (int sp = 1; sp < m; sp++) {
            St s; memset(&s, 0, sizeof s);
            for (int i = 0; i < sp; i++) push(&s, 0, w[i]);
            for (int i = sp; i < m; i++) push(&s, 1, w[i]);
            long pb = cycle_through(&s, maxb, 0, NULL);
            if (!pb) continue;
            nbase++; cbase += 1.0 / pb;
            /* apply the doubling ed times: D(w) = interleave(w, w+1) */
            int a1[CAP], a2[CAP], l1 = sp, l2 = m - sp, t1[CAP], t2[CAP];
            for (int i = 0; i < sp; i++) a1[i] = w[i];
            for (int i = sp; i < m; i++) a2[i - sp] = w[i];
            for (int e = 0; e < ed; e++) {
                for (int i = 0; i < l1; i++) { t1[2*i] = a1[i]; t1[2*i+1] = a1[i] + 1; }
                for (int i = 0; i < l2; i++) { t2[2*i] = a2[i]; t2[2*i+1] = a2[i] + 1; }
                l1 *= 2; l2 *= 2;
                for (int i = 0; i < l1; i++) a1[i] = t1[i];
                for (int i = 0; i < l2; i++) a2[i] = t2[i];
            }
            St d; memset(&d, 0, sizeof d);
            for (int i = 0; i < l1; i++) push(&d, 0, a1[i]);
            for (int i = 0; i < l2; i++) push(&d, 1, a2[i]);
            int all;
            long pd = enters_loop(&d, ed >= 2 ? 200000000L : maxd, runlen, &all);
            if (!pd) continue;
            ndbl++; cdbl += 1.0 / pd;
            if (all < 0) { nunk++; continue; }
            if (!all) {
                nnew++; cnew += 1.0 / pd;
                #pragma omp critical
                { if (ex_w < 0) { ex_w = wi; ex_s = sp; } }
            }
        }
    }
    printf("doublings=%d n=%d | m=%d letters=%d: base positions %lld (distinct base cycles %.2f) | doubled game enters a tie-free loop: %lld (%.2f by 1/loop-length) | doubled loop NEW-type: %lld positions (%.2f) | run-check skipped (long): %lld\n",
           ed, m << ed, m, L, nbase, cbase, ndbl, cdbl, nnew, cnew, nunk);
    if (ex_w >= 0) {
        long long x = ex_w; char P[CAP + 1];
        for (int i = 0; i < m; i++) { P[i] = 'A' + (int)(x % L); x /= L; }
        P[m] = 0;
        printf("   example base: P1 = %.*s  P2 = %s\n", ex_s, P, P + ex_s);
    }
    return 0;
}
