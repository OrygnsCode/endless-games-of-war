/* Random sample of War positions (or deals), CPU, OpenMP.
   Each sample is a random order of the cards 1..n with a random split point (mode pos), or a deal
   with ceil(n/2) cards to player 1 (mode deal). The game is played (winning card, then losing card,
   under the winner's pile) until it ends, a loop is detected (Brent), or the step cap is hit.
   Every loop is walked once and classified: it is of Spivey's Theorem-3 type iff every maximal run
   of consecutive wins has length exactly 2^v = n & -n. Loop lengths are tallied and tested for
   divisibility by n + 2^v. Loops not of Theorem-3 type are also sorted by Spivey's categories
   (a card that never loses is in category A; otherwise its category is one below the lowest category
   of the cards that beat it), and the period of card 1 is found for each of them.
   When n = 2^(j+1) (4k+3) with k >= 1, each such loop is also tested for membership in the doubled
   family: with every card replaced by its category letter, the loop must pass through the family start,
   player 1 holding T^k and player 2 holding Z T^k Y (T = D^j(ABBC), Z = D^j(DE), Y = D^j(CDDE), where D
   replaces each letter x by x followed by the next letter), or through it with the players exchanged.
   Samples are drawn in blocks of 256, and each block has its own generator seeded from (seed, block
   index), so the output does not depend on the number of threads. With the optional last argument
   "list", the position on every loop not of Theorem-3 type is printed as well, in sample order.
   Usage: sampler n samples threads seed [pos|deal] [cap] [list]
   Build: gcc -O3 -march=native -fopenmp -o sampler sampler.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <omp.h>

#define CAP 128                 /* ring capacity per pile (n <= 127) */
#define BLOCK 256
typedef struct { uint8_t c[2][CAP]; uint8_t h[2], len[2]; } St;

static inline uint64_t xs(uint64_t *s) { uint64_t x = *s; x ^= x << 13; x ^= x >> 7; x ^= x << 17; return *s = x; }
static inline uint64_t splitmix(uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31);
}
static inline int top(const St *s, int p) { return s->c[p][s->h[p]]; }
static inline void push(St *s, int p, int v) { s->c[p][(s->h[p] + s->len[p]) & (CAP - 1)] = (uint8_t)v; s->len[p]++; }
static inline int step(St *s) {           /* returns the winner, 0 or 1 */
    int a = top(s, 0), b = top(s, 1);
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
#define MAXL 256
typedef struct { long long L; long long count; int other; } LEnt;
static int cmp_ent(const void *x, const void *y) {
    const LEnt *a = x, *b = y;
    if (a->other != b->other) return a->other - b->other;
    return (a->L > b->L) - (a->L < b->L);
}

/* Spivey's categories on the loop through s0 (length L): cat[c] for every card (0 = A), and their sizes as
   "a,b,c,...", A first. */
static void categories(const St *s0, long long L, int n, int *cat, char *out) {
    uint64_t by[CAP][2];                  /* by[c]: the cards that beat card c somewhere on the loop */
    memset(by, 0, sizeof by);
    St u = *s0;
    for (long long t = 0; t < L; t++) {
        int a = top(&u, 0), b = top(&u, 1), w = a > b ? a : b, l = a > b ? b : a;
        by[l][w >> 6] |= 1ULL << (w & 63);
        step(&u);
    }
    int cnt[CAP] = {0}, top_cat = 0;
    for (int c = n; c >= 1; c--) {     /* every card that beats c is higher, so its category is known */
        int m = -1;
        for (int w = c + 1; w <= n; w++) if (by[c][w >> 6] >> (w & 63) & 1 && cat[w] > m) m = cat[w];
        cat[c] = m + 1; cnt[cat[c]]++;
        if (cat[c] > top_cat) top_cat = cat[c];
    }
    int k = 0;
    for (int i = 0; i <= top_cat; i++) k += sprintf(out + k, i ? ",%d" : "%d", cnt[i]);
}
/* The doubled family's start for this n, as letters (0 = A); fam_n1 = 0 if n is not of the family form. */
static int fam1[CAP], fam2[CAP], fam_n1 = 0, fam_n2 = 0;
static int dj(const int *w, int m, int j, int *out) {
    int a[CAP], b[CAP];
    memcpy(a, w, m * sizeof(int));
    for (int t = 0; t < j; t++) {
        if (2 * m > CAP) return -1;
        for (int i = 0; i < m; i++) { b[2 * i] = a[i]; b[2 * i + 1] = a[i] + 1; }
        m *= 2; memcpy(a, b, m * sizeof(int));
    }
    memcpy(out, a, m * sizeof(int));
    return m;
}
static void build_family(int n) {
    if (n % 2) return;
    int j = 0; while (!((n >> (j + 1)) & 1)) j++;          /* n = 2^(j+1) m with m odd */
    int m = n >> (j + 1);
    if (m % 4 != 3 || m < 7) return;
    int k = (m - 3) / 4;
    const int T0[] = {0, 1, 1, 2}, Z0[] = {3, 4}, Y0[] = {2, 3, 3, 4};
    int T[CAP], Z[CAP], Y[CAP];
    int lt = dj(T0, 4, j, T), lz = dj(Z0, 2, j, Z), ly = dj(Y0, 4, j, Y);
    if (lt < 0 || lz < 0 || ly < 0) return;
    int a = 0, b = 0;
    for (int r = 0; r < k; r++) for (int i = 0; i < lt; i++) fam1[a++] = T[i];
    for (int i = 0; i < lz; i++) fam2[b++] = Z[i];
    for (int r = 0; r < k; r++) for (int i = 0; i < lt; i++) fam2[b++] = T[i];
    for (int i = 0; i < ly; i++) fam2[b++] = Y[i];
    if (a + b == n) { fam_n1 = a; fam_n2 = b; }
}
static int pile_is(const St *s, int p, const int *cat, const int *word, int m) {
    if (s->len[p] != m) return 0;
    for (int i = 0; i < m; i++) if (cat[s->c[p][(s->h[p] + i) & (CAP - 1)]] != word[i]) return 0;
    return 1;
}
static int in_family(const St *s0, long long L, const int *cat) {
    if (!fam_n1) return 0;
    St u = *s0;
    for (long long t = 0; t < L; t++) {
        if (pile_is(&u, 0, cat, fam1, fam_n1) && pile_is(&u, 1, cat, fam2, fam_n2)) return 1;
        if (pile_is(&u, 1, cat, fam1, fam_n1) && pile_is(&u, 0, cat, fam2, fam_n2)) return 1;
        step(&u);
    }
    return 0;
}
static int place_of_1(const St *s) {     /* pile * CAP + depth of card 1 */
    for (int p = 0; p < 2; p++)
        for (int i = 0; i < s->len[p]; i++)
            if (s->c[p][(s->h[p] + i) & (CAP - 1)] == 1) return p * CAP + i;
    return -1;
}
/* Period of card 1 on the loop through s0 of length L: the least p dividing L such that card 1's place
   after t and after t + p turns agree for every t. */
static long long card1_period(const St *s0, long long L) {
    for (long long p = 1; p <= L; p++) {
        if (L % p) continue;
        St a = *s0, b = *s0; int ok = 1;
        for (long long t = 0; t < p; t++) step(&b);
        for (long long t = 0; t < L && ok; t++) { if (place_of_1(&a) != place_of_1(&b)) ok = 0; step(&a); step(&b); }
        if (ok) return p;
    }
    return L;
}
#define MAXC 256
typedef struct { long long L; char sizes[400]; long long count, fam, c1ok, ex_i; St ex; } CEnt;
static int cmp_cls(const void *x, const void *y) {
    const CEnt *a = x, *b = y;
    if (a->L != b->L) return (a->L > b->L) - (a->L < b->L);
    return strcmp(a->sizes, b->sizes);
}

#define MAXLIST 100000
typedef struct { long long i; uint8_t len[2]; uint8_t c[2][CAP]; } Listed;
static int cmp_listed(const void *x, const void *y) {
    const Listed *a = x, *b = y;
    return (a->i > b->i) - (a->i < b->i);
}

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: sampler n samples threads seed [pos|deal] [cap] [list]\n"); return 1; }
    int n = atoi(argv[1]); long long N = atoll(argv[2]); int th = atoi(argv[3]); uint64_t seed = strtoull(argv[4], 0, 10);
    int deal = (argc > 5 && strcmp(argv[5], "deal") == 0);
    long long cap = argc > 6 ? atoll(argv[6]) : 20000000LL;
    int list = (argc > 7 && strcmp(argv[7], "list") == 0);
    static Listed listed[MAXLIST]; long long nlisted = 0, unlisted = 0;
    if (n < 2 || n >= CAP) { fprintf(stderr, "need 2 <= n <= %d\n", CAP - 1); return 1; }
    int v = n & -n;
    long long ended = 0, looped = 0, capped = 0, other = 0, notdiv = 0, untallied = 0;
    LEnt tab[MAXL]; int ntab = 0;
    static CEnt cls[MAXC]; int ncls = 0; long long unclassed = 0;
    long long nblocks = (N + BLOCK - 1) / BLOCK;
    build_family(n);
    omp_set_num_threads(th);
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:ended,looped,capped,other,notdiv)
    for (long long blk = 0; blk < nblocks; blk++) {
        uint64_t rs = splitmix(splitmix(seed) ^ (uint64_t)blk);
        if (rs == 0) rs = 1;
        long long hi = (blk + 1) * BLOCK < N ? (blk + 1) * BLOCK : N;
        for (long long i = blk * BLOCK; i < hi; i++) {
            int perm[CAP];
            for (int k = 0; k < n; k++) perm[k] = k + 1;
            for (int k = n - 1; k > 0; k--) { int r = (int)(xs(&rs) % (uint64_t)(k + 1)); int t = perm[k]; perm[k] = perm[r]; perm[r] = t; }
            int split = deal ? (n + 1) / 2 : 1 + (int)(xs(&rs) % (uint64_t)(n - 1));
            St s; memset(&s, 0, sizeof s);
            for (int k = 0; k < split; k++) push(&s, 0, perm[k]);
            for (int k = split; k < n; k++) push(&s, 1, perm[k]);

            St saved = s; long long power = 1, lam = 0, steps = 0; int done = 0;
            while (1) {
                step(&s); steps++; lam++;
                if (s.len[0] == 0 || s.len[1] == 0) { ended++; done = 1; break; }
                if (eq(&s, &saved)) break;
                if (lam == power) { saved = s; power <<= 1; lam = 0; }
                if (steps > cap) { capped++; done = 1; break; }
            }
            if (done) continue;
            looped++;
            /* s is on the loop and lam is its length. Advance to the first turn after a change of
               winner, then count the runs of wins over exactly lam turns, cyclically. */
            long long L = lam;
            St u = s;
            int prev = step(&u);
            for (long long k = 1; k < L; k++) { int w = step(&u); if (w != prev) { prev = w; break; } }
            int run = 1, bad = 0;
            for (long long k = 1; k < L; k++) {
                int w = step(&u);
                if (w == prev) run++;
                else { if (run != v) bad = 1; prev = w; run = 1; }
            }
            if (run != v) bad = 1;
            if (bad) other++;
            if (L % (n + v) != 0) notdiv++;
            char sizes[400]; int cat[CAP], fam = 0, c1ok = 0;
            if (bad) {
                categories(&s, L, n, cat, sizes);
                fam = in_family(&s, L, cat);
                c1ok = card1_period(&s, L) == n + v;
            }
            #pragma omp critical
            {
                int f = -1;
                for (int t = 0; t < ntab; t++) if (tab[t].L == L && tab[t].other == bad) { f = t; break; }
                if (f < 0 && ntab < MAXL) { tab[ntab].L = L; tab[ntab].count = 0; tab[ntab].other = bad; f = ntab++; }
                if (f >= 0) tab[f].count++; else untallied++;
                if (bad) {
                    int g = -1;
                    for (int q = 0; q < ncls; q++) if (cls[q].L == L && strcmp(cls[q].sizes, sizes) == 0) { g = q; break; }
                    if (g < 0 && ncls < MAXC) { cls[ncls].L = L; strcpy(cls[ncls].sizes, sizes); cls[ncls].count = 0; cls[ncls].fam = 0; cls[ncls].c1ok = 0; cls[ncls].ex_i = -1; g = ncls++; }
                    if (g < 0) unclassed++;
                    else {
                        cls[g].count++; cls[g].fam += fam; cls[g].c1ok += c1ok;
                        if (cls[g].ex_i < 0 || i < cls[g].ex_i) { cls[g].ex_i = i; cls[g].ex = s; }
                    }
                    if (list) {
                        if (nlisted < MAXLIST) {
                            Listed *e = &listed[nlisted++]; e->i = i;
                            for (int p = 0; p < 2; p++) {
                                e->len[p] = s.len[p];
                                for (int k = 0; k < s.len[p]; k++) e->c[p][k] = s.c[p][(s.h[p] + k) & (CAP - 1)];
                            }
                        } else unlisted++;
                    }
                }
            }
        }
    }
    qsort(tab, ntab, sizeof tab[0], cmp_ent);
    printf("n=%d (2^v=%d) mode=%s samples=%lld seed=%llu: ended %lld, looped %lld, capped %lld | loops not of Theorem-3 type %lld | loop length not a multiple of n+2^v: %lld\n",
           n, v, deal ? "deal" : "pos", N, (unsigned long long)seed, ended, looped, capped, other, notdiv);
    for (int t = 0; t < ntab; t++) printf("   L=%lld x%lld%s\n", tab[t].L, tab[t].count, tab[t].other ? "   not Theorem-3 type" : "");
    if (untallied) printf("   (%lld loops with lengths beyond the first %d distinct ones are not listed)\n", untallied, MAXL);
    if (ncls) {
        qsort(cls, ncls, sizeof cls[0], cmp_cls);
        printf("   loops not of Theorem-3 type, by length and category sizes (A first): how many pass through the doubled-family start, how many give card 1 period n+2^v, and the first example:\n");
        for (int q = 0; q < ncls; q++) {
            const St *e = &cls[q].ex;
            printf("   L=%lld sizes %s x%lld", cls[q].L, cls[q].sizes, cls[q].count);
            if (fam_n1) printf(" | doubled family %lld", cls[q].fam);
            printf(" | card 1 period n+2^v %lld | sample %lld: P1 =", cls[q].c1ok, cls[q].ex_i);
            for (int i = 0; i < e->len[0]; i++) printf(" %d", e->c[0][(e->h[0] + i) & (CAP - 1)]);
            printf("  P2 =");
            for (int i = 0; i < e->len[1]; i++) printf(" %d", e->c[1][(e->h[1] + i) & (CAP - 1)]);
            printf("\n");
        }
        if (unclassed) printf("   (%lld loops in classes beyond the first %d are not listed)\n", unclassed, MAXC);
    }
    if (list) {
        qsort(listed, nlisted, sizeof listed[0], cmp_listed);
        printf("   position on each loop not of Theorem-3 type, in sample order (sample: P1 | P2):\n");
        for (long long q = 0; q < nlisted; q++) {
            printf("   %lld:", listed[q].i);
            for (int k = 0; k < listed[q].len[0]; k++) printf(" %d", listed[q].c[0][k]);
            printf(" |");
            for (int k = 0; k < listed[q].len[1]; k++) printf(" %d", listed[q].c[1][k]);
            printf("\n");
        }
        if (unlisted) printf("   (%lld more loops not listed)\n", unlisted);
    }
    return 0;
}
