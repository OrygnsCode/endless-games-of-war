/* Checks whether every War cycle is reached by an ordinary deal. CPU, OpenMP, n <= 15.
   1. Enumerate the distinct cycles up to swap exactly as distinct_cycles.c: each cycle containing a
      canonical position (player 1's top card is n) is counted at its minimal canonical key.
   2. For each such cycle, search backwards from its positions for a position of deal size: player 1 holds
      ceil(n/2) and player 2 floor(n/2), or the reverse (the reverse means a standard deal reaches the
      swapped cycle, which is the same class up to swap). A position has at most two predecessors: undo a
      player-1 win (player 1's last two cards w > l: put w back on top of player 1 and l on top of player 2)
      or a player-2 win. Every position has a unique successor, so off the loop the predecessors form a
      finite tree; no visited set is needed. The search stops at the first deal-size position.
   Output: number of classes, how many are reached by a deal, how many are not, and loop lengths of those
   not reached. A cap on the number of positions visited per cycle marks a class "undetermined".
   Usage: reach_cycles n threads [cap]     Build: gcc -O3 -march=native -fopenmp -o reach_cycles reach_cycles.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <omp.h>

typedef struct { uint64_t p[2]; int len[2]; } St;
static int n;
static inline int step(St *s) {
    int a = (int)(s->p[0] & 15), b = (int)(s->p[1] & 15);
    s->p[0] >>= 4; s->p[1] >>= 4; s->len[0]--; s->len[1]--;
    if (a > b) { s->p[0] |= ((uint64_t)a << (4 * s->len[0])) | ((uint64_t)b << (4 * (s->len[0] + 1))); s->len[0] += 2; return 0; }
    s->p[1] |= ((uint64_t)b << (4 * s->len[1])) | ((uint64_t)a << (4 * (s->len[1] + 1))); s->len[1] += 2; return 1;
}
static inline int same(const St *x, const St *y) { return x->len[0] == y->len[0] && x->p[0] == y->p[0] && x->p[1] == y->p[1]; }
static inline uint64_t key(const St *s) {
    uint64_t k = (uint64_t)s->len[0] << 60; int pos = 56;
    for (int p = 0; p < 2; p++) { uint64_t v = s->p[p]; for (int i = 0; i < s->len[p]; i++) { k |= (v & 15) << pos; v >>= 4; pos -= 4; } }
    return k;
}
static inline St swapst(const St *s) { St t; t.p[0] = s->p[1]; t.p[1] = s->p[0]; t.len[0] = s->len[1]; t.len[1] = s->len[0]; return t; }
static inline int topc(const St *s, int p) { return (int)(s->p[p] & 15); }
static inline int dealsize(const St *s) { int h = n / 2, H = (n + 1) / 2; return (s->len[0] == H && s->len[1] == h) || (s->len[0] == h && s->len[1] == H); }
/* predecessor by undoing a win of player w (0/1); returns 0 if impossible */
static inline int undo(const St *s, int w, St *out) {
    int L = s->len[w]; if (L < 2) return 0;
    int cw = (int)((s->p[w] >> (4 * (L - 2))) & 15), cl = (int)((s->p[w] >> (4 * (L - 1))) & 15);
    if (cw <= cl) return 0;
    *out = *s;
    out->p[w] &= (L - 2 > 0) ? ((((uint64_t)1) << (4 * (L - 2))) - 1) : 0; out->len[w] = L - 2;
    out->p[w] = (out->p[w] << 4) | (uint64_t)cw; out->len[w]++;
    int o = 1 - w;
    out->p[o] = (out->p[o] << 4) | (uint64_t)cl; out->len[o]++;
    return 1;
}
/* returns 1 if some deal-size position reaches the loop through s0 (loop length lam), 0 if none, -1 if capped */
static int reached(const St *s0, long lam, long cap) {
    St *stack = malloc(sizeof(St) * (1 << 18)); long sp = 0, visited = 0; int res = 0;
    St prev = *s0;                       /* previous loop state of s0: step lam-1 times */
    for (long i = 0; i < lam - 1; i++) step(&prev);
    St t = *s0;
    for (long i = 0; i < lam && !res; i++) {       /* t runs around the loop; prev is its loop predecessor */
        if (dealsize(&t)) { res = 1; break; }
        for (int w = 0; w < 2 && !res; w++) {
            St q; if (!undo(&t, w, &q) || same(&q, &prev)) continue;
            sp = 0; stack[sp++] = q;
            while (sp > 0) {
                St u = stack[--sp]; visited++;
                if (dealsize(&u)) { res = 1; break; }
                if (visited > cap) { free(stack); return -1; }
                for (int w2 = 0; w2 < 2; w2++) { St r; if (undo(&u, w2, &r)) { if (sp < (1 << 18)) stack[sp++] = r; else { free(stack); return -1; } } }
            }
        }
        prev = t; step(&t);
    }
    free(stack);
    return res;
}
int main(int argc, char **argv) {
    n = atoi(argv[1]); int th = atoi(argv[2]); long cap = argc > 3 ? atol(argv[3]) : 200000000L;
    int m = n - 1; long long fact = 1; for (int i = 2; i <= m; i++) fact *= i;
    long long classes = 0, yes = 0, no = 0, und = 0;
    long long nolen[4096] = {0};
    omp_set_num_threads(th);
    #pragma omp parallel for schedule(dynamic, 256) reduction(+:classes,yes,no,und)
    for (long long idx = 0; idx < fact; idx++) {
        int avail[16], perm[16]; for (int i = 0; i < m; i++) avail[i] = i + 1;
        long long x = idx; int na = m;
        for (int i = 0; i < m; i++) {
            long long f = 1; for (int t2 = 2; t2 <= m - 1 - i; t2++) f *= t2;
            int d = (int)(x / f); x %= f;
            perm[i] = avail[d]; for (int t2 = d; t2 < na - 1; t2++) avail[t2] = avail[t2 + 1]; na--;
        }
        for (int j = 0; j <= n - 2; j++) {
            St s; s.p[0] = (uint64_t)n; for (int i = 0; i < j; i++) s.p[0] |= (uint64_t)perm[i] << (4 * (i + 1));
            s.len[0] = 1 + j; s.p[1] = 0; s.len[1] = 0;
            for (int i = j; i < m; i++) { s.p[1] |= (uint64_t)perm[i] << (4 * s.len[1]); s.len[1]++; }
            St t = s, saved = s; long power = 1, lam = 0; int ended = 0;
            while (1) {
                step(&t); lam++;
                if (t.len[0] == 0 || t.len[1] == 0) { ended = 1; break; }
                if (same(&t, &saved)) break;
                if (lam == power) { saved = t; power <<= 1; lam = 0; }
            }
            if (ended) continue;
            St u = s; for (long i = 0; i < lam; i++) step(&u);
            if (!same(&u, &s)) continue;
            uint64_t K = UINT64_MAX; St w = s;
            for (long i = 0; i < lam; i++) {
                if (topc(&w, 0) == n) { uint64_t k = key(&w); if (k < K) K = k; }
                if (topc(&w, 1) == n) { St sw = swapst(&w); uint64_t k = key(&sw); if (k < K) K = k; }
                step(&w);
            }
            if (key(&s) != K) continue;
            classes++;
            int r = reached(&s, lam, cap);
            if (r == 1) yes++;
            else if (r == 0) {
                no++;
                #pragma omp atomic
                nolen[lam < 4095 ? lam : 4095]++;
            } else und++;
        }
    }
    printf("n=%d: distinct cycles up to swap %lld | reached by a deal %lld | NOT reached %lld | undetermined (cap %ld) %lld\n", n, classes, yes, no, cap, und);
    if (no) { printf("   loop lengths of cycles not reached:"); for (int L = 0; L < 4096; L++) if (nolen[L]) printf(" %d:%lld", L, nolen[L]); printf("\n"); }
    return 0;
}
