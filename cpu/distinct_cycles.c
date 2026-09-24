/* Distinct War cycles up to swapping the players, n <= 15. CPU, OpenMP.
   Method (different from the per-cycle weights of gpu/war_gpu.py): every cycle, up to swap, contains a position where
   player 1's top card is n (canonical position). For every canonical position s we test whether s lies
   on its own cycle (Brent gives the loop length lam; s is on the loop iff lam steps from s return to s).
   If so we walk the loop and compute K = the minimum 64-bit key over
     { key(t) : t on the loop, player 1's top card is n }  union  { key(swap(t)) : t on the loop, player 2's top is n }.
   s is counted iff key(s) == K. So each cycle-class {C, swap(C)} is counted exactly once.
   Piles are packed 4 bits per card (top card in the low nibble), so n <= 15.
   Usage: distinct_cycles n threads     Build: gcc -O3 -march=native -fopenmp -o distinct_cycles distinct_cycles.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <omp.h>

typedef struct { uint64_t p[2]; int len[2]; } St;
static inline int step(St *s) {
    int a = (int)(s->p[0] & 15), b = (int)(s->p[1] & 15);
    s->p[0] >>= 4; s->p[1] >>= 4; s->len[0]--; s->len[1]--;
    if (a > b) { s->p[0] |= ((uint64_t)a << (4 * s->len[0])) | ((uint64_t)b << (4 * (s->len[0] + 1))); s->len[0] += 2; return 0; }
    s->p[1] |= ((uint64_t)b << (4 * s->len[1])) | ((uint64_t)a << (4 * (s->len[1] + 1))); s->len[1] += 2; return 1;
}
static inline int same(const St *x, const St *y) { return x->len[0] == y->len[0] && x->p[0] == y->p[0] && x->p[1] == y->p[1]; }
/* key: player 1's length in the top 4 bits, then player 1's cards then player 2's, all top first */
static inline uint64_t key(const St *s) {
    uint64_t k = (uint64_t)s->len[0] << 60; int pos = 56;
    for (int p = 0; p < 2; p++) {
        uint64_t v = s->p[p];
        for (int i = 0; i < s->len[p]; i++) { k |= (v & 15) << pos; v >>= 4; pos -= 4; }
    }
    return k;
}
static inline St swapst(const St *s) { St t; t.p[0] = s->p[1]; t.p[1] = s->p[0]; t.len[0] = s->len[1]; t.len[1] = s->len[0]; return t; }
static inline int topc(const St *s, int p) { return (int)(s->p[p] & 15); }

int main(int argc, char **argv) {
    int n = atoi(argv[1]), th = atoi(argv[2]);
    int m = n - 1; long long fact = 1; for (int i = 2; i <= m; i++) fact *= i;
    long long distinct = 0, oncycle = 0, cycling = 0;
    long long lenhist[4096] = {0};
    omp_set_num_threads(th);
    #pragma omp parallel for schedule(dynamic, 1024) reduction(+:distinct,oncycle,cycling)
    for (long long idx = 0; idx < fact; idx++) {
        /* decode permutation of 1..n-1 from idx (Lehmer code) */
        int avail[16], perm[16]; for (int i = 0; i < m; i++) avail[i] = i + 1;
        long long x = idx; int na = m;
        for (int i = 0; i < m; i++) {
            long long f = 1; for (int t = 2; t <= m - 1 - i; t++) f *= t;
            int d = (int)(x / f); x %= f;
            perm[i] = avail[d]; for (int t = d; t < na - 1; t++) avail[t] = avail[t + 1]; na--;
        }
        for (int j = 0; j <= n - 2; j++) {
            St s; s.p[0] = (uint64_t)n; s.len[0] = 1;
            for (int i = 0; i < j; i++) s.p[0] |= (uint64_t)perm[i] << (4 * (i + 1));
            s.len[0] = 1 + j; s.p[1] = 0; s.len[1] = 0;
            for (int i = j; i < m; i++) { s.p[1] |= (uint64_t)perm[i] << (4 * s.len[1]); s.len[1]++; }
            /* Brent from s */
            St t = s, saved = s; long power = 1, lam = 0; int ended = 0;
            while (1) {
                step(&t); lam++;
                if (t.len[0] == 0 || t.len[1] == 0) { ended = 1; break; }
                if (same(&t, &saved)) break;
                if (lam == power) { saved = t; power <<= 1; lam = 0; }
            }
            if (ended) continue;
            cycling++;
            /* is s on its own loop? */
            St u = s; for (long i = 0; i < lam; i++) step(&u);
            if (!same(&u, &s)) continue;
            oncycle++;
            uint64_t K = UINT64_MAX; St w = s;
            for (long i = 0; i < lam; i++) {
                if (topc(&w, 0) == n) { uint64_t k = key(&w); if (k < K) K = k; }
                if (topc(&w, 1) == n) { St sw = swapst(&w); uint64_t k = key(&sw); if (k < K) K = k; }
                step(&w);
            }
            if (key(&s) == K) {
                distinct++;
                #pragma omp atomic
                lenhist[lam < 4095 ? lam : 4095]++;
            }
        }
    }
    printf("n=%d: canonical positions that never end %lld; on a cycle %lld; DISTINCT cycles up to swap %lld\n", n, cycling, oncycle, distinct);
    printf("   cycle lengths (distinct cycles):");
    for (int L = 0; L < 4096; L++) if (lenhist[L]) printf(" %d:%lld", L, lenhist[L]);
    printf("\n");
    return 0;
}
