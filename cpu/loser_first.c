/* War with the loser-first put-back rule, n <= 15. CPU, OpenMP.
   Each turn both players show their top card; the higher card wins; the losing card and then the winning
   card go under the winner's pile. A deal: an ordering of cards 1..n, player 1 gets the first ceil(n/2)
   cards (top first), player 2 the rest. Counts the deals whose game never ends (Brent cycle detection),
   and the longest game that ends. Work is split by the first two cards (n*(n-1) chunks); within a chunk the
   remaining n-2 cards run through all orders in lexicographic order (next_permutation).
   Piles are packed 4 bits per card, top card in the low nibble.
   Each finished chunk prints a line "chunk c0 c1 deals never_end longest" to stderr (flushed), so a long run
   can be checked while it runs, and summed if it is interrupted.
   Usage: loser_first n threads      Build: gcc -O3 -march=native -fopenmp -o loser_first loser_first.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <omp.h>

typedef struct { uint64_t p[2]; int len[2]; } St;
static inline void turn(St *s) {
    int a = (int)(s->p[0] & 15), b = (int)(s->p[1] & 15);
    s->p[0] >>= 4; s->p[1] >>= 4; s->len[0]--; s->len[1]--;
    int w = a > b ? 0 : 1, hi = a > b ? a : b, lo = a > b ? b : a;
    s->p[w] |= ((uint64_t)lo << (4 * s->len[w])) | ((uint64_t)hi << (4 * (s->len[w] + 1)));   /* loser first */
    s->len[w] += 2;
}
static inline int same(const St *x, const St *y) { return x->len[0] == y->len[0] && x->p[0] == y->p[0] && x->p[1] == y->p[1]; }
static int next_perm(int *a, int k) {
    int i = k - 2; while (i >= 0 && a[i] >= a[i + 1]) i--;
    if (i < 0) return 0;
    int j = k - 1; while (a[j] <= a[i]) j--;
    int t = a[i]; a[i] = a[j]; a[j] = t;
    for (int l = i + 1, r = k - 1; l < r; l++, r--) { t = a[l]; a[l] = a[r]; a[r] = t; }
    return 1;
}
int main(int argc, char **argv) {
    int n = atoi(argv[1]), th = atoi(argv[2]);
    int H = (n + 1) / 2;
    long long cyc = 0, total = 0; long longest = 0;
    omp_set_num_threads(th);
    #pragma omp parallel for collapse(2) schedule(dynamic, 1) reduction(+:cyc,total) reduction(max:longest)
    for (int c0 = 1; c0 <= n; c0++)
        for (int c1 = 1; c1 <= n; c1++) {
            if (c1 == c0 || n < 2) continue;
            int rest[16], k = 0; long long ccyc = 0, ctot = 0; long clong = 0;
            for (int v = 1; v <= n; v++) if (v != c0 && v != c1) rest[k++] = v;
            do {
                int d[16]; d[0] = c0; d[1] = c1; for (int i = 0; i < k; i++) d[2 + i] = rest[i];
                St s; s.p[0] = s.p[1] = 0; s.len[0] = s.len[1] = 0;
                for (int i = 0; i < n; i++) { int p = i < H ? 0 : 1; s.p[p] |= (uint64_t)d[i] << (4 * s.len[p]); s.len[p]++; }
                ctot++;
                St saved = s; long power = 1, lam = 0, t = 0; int ended = 0;
                while (1) {
                    turn(&s); t++; lam++;
                    if (s.len[0] == 0 || s.len[1] == 0) { ended = 1; break; }
                    if (same(&s, &saved)) break;
                    if (lam == power) { saved = s; power <<= 1; lam = 0; }
                }
                if (ended) { if (t > clong) clong = t; }
                else ccyc++;
            } while (next_perm(rest, k));
            total += ctot; cyc += ccyc; if (clong > longest) longest = clong;
            #pragma omp critical
            { fprintf(stderr, "chunk %d %d %lld %lld %ld\n", c0, c1, ctot, ccyc, clong); fflush(stderr); }
        }
    if (n == 1) { total = 1; }
    printf("loser-first n=%d: deals %lld, never end %lld, longest ending game %ld\n", n, total, cyc, longest);
    return 0;
}
