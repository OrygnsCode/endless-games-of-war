/* Letter bases and their doublings: a second, independently written base search, used to confirm base_search.c.
   Letters 0..L-1 (0 = A, strongest; L = 4 unless given). A base is a position (P1, P2) with m letters in all whose
   letter game returns to it with no tie (two equal letters meeting) and no empty pile. For e = 1, 2, 3 the base is
   doubled e times, D(w) = w interleaved with w + 1, and the doubled game is played until it repeats (a tie or an
   empty pile means no loop). The loop is "not of Theorem-3 type" when its runs of wins are not all of length 2^e.
   Mode "full": every word and every split, for comparing counts with base_search.c. Mode "canon": only words whose
   first letter is A (every letter cycle containing an A passes through such a position, up to exchanging the
   players), and every base whose doubling is not of Theorem-3 type is listed, sorted, as "NEW e m P1 P2". With the
   optional fifth argument "list", full mode lists them too (the default output of full mode is unchanged).
   usage: base_enum m full|canon threads [letters [list]]
   build: gcc -O3 -march=native -fopenmp -o base_enum base_enum.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#ifdef _WIN32
#include <windows.h>
#endif

#define CAP 1024
typedef struct { unsigned char a[CAP], b[CAP]; int ha, la, hb, lb; } G;

static int turn(G *g) {                      /* returns 1 or 2 (winner), 0 on a tie */
    int x = g->a[g->ha], y = g->b[g->hb];
    if (x == y) return 0;
    g->ha = (g->ha + 1) % CAP; g->la--; g->hb = (g->hb + 1) % CAP; g->lb--;
    if (x < y) { g->a[(g->ha + g->la) % CAP] = x; g->a[(g->ha + g->la + 1) % CAP] = y; g->la += 2; return 1; }
    g->b[(g->hb + g->lb) % CAP] = y; g->b[(g->hb + g->lb + 1) % CAP] = x; g->lb += 2; return 2;
}
static int same(const G *g, const G *h) {
    if (g->la != h->la) return 0;
    for (int i = 0; i < g->la; i++) if (g->a[(g->ha + i) % CAP] != h->a[(h->ha + i) % CAP]) return 0;
    for (int i = 0; i < g->lb; i++) if (g->b[(g->hb + i) % CAP] != h->b[(h->hb + i) % CAP]) return 0;
    return 1;
}
static void load(G *g, const int *p1, int n1, const int *p2, int n2) {
    g->ha = g->hb = 0; g->la = n1; g->lb = n2;
    for (int i = 0; i < n1; i++) g->a[i] = (unsigned char)p1[i];
    for (int i = 0; i < n2; i++) g->b[i] = (unsigned char)p2[i];
}
static char **lines; static long nlines, caplines;
static void keep(const char *s) {
    if (nlines == caplines) { caplines = caplines ? 2 * caplines : 256; lines = realloc(lines, sizeof(char *) * caplines); }
    lines[nlines++] = strdup(s);
}
static int cmp(const void *x, const void *y) { return strcmp(*(char *const *)x, *(char *const *)y); }
/* 1 if the game returns to its start within cap turns with no tie and no empty pile */
static int returns(const G *start, long cap) {
    G g = *start;
    for (long t = 1; t <= cap; t++) {
        if (!turn(&g) || g.la == 0 || g.lb == 0) return 0;
        if (same(&g, start)) return 1;
    }
    return 0;
}
/* play until a repeat (Brent); 0 if tie / empty / cap; else loop length, and *t3 = 1 if all runs have length r */
static long loop_runs(const G *start, long cap, int r, int *t3) {
    G g = *start, s = *start; long power = 1, lam = 0, t = 0;
    for (;;) {
        if (!turn(&g) || g.la == 0 || g.lb == 0) return 0;
        t++; lam++;
        if (same(&g, &s)) break;
        if (lam == power) { s = g; power *= 2; lam = 0; }
        if (t > cap) return 0;
    }
    int *w = malloc(sizeof(int) * lam); G u = g;
    for (long i = 0; i < lam; i++) w[i] = turn(&u);
    long k = -1;
    for (long i = 0; i < lam; i++) if (w[i] != w[(i + lam - 1) % lam]) { k = i; break; }
    int ok = (k >= 0);
    if (ok) {
        long run = 0;
        for (long i = 0; i < lam; i++) {
            if (i > 0 && w[(k + i) % lam] != w[(k + i - 1) % lam]) { if (run != r) ok = 0; run = 0; }
            run++;
        }
        if (run != r) ok = 0;
    }
    free(w); *t3 = ok; return lam;
}

int main(int argc, char **argv) {
    int m = atoi(argv[1]), canon = !strcmp(argv[2], "canon"), th = atoi(argv[3]);
    int NL = argc > 4 ? atoi(argv[4]) : 4;
    int list = canon || (argc > 5 && !strcmp(argv[5], "list"));
#ifdef _WIN32
    SetPriorityClass(GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS);   /* stay out of the way of interactive work */
#endif
    long long words = 1; for (int i = 0; i < (canon ? m - 1 : m); i++) words *= NL;
    long long nbase = 0, nloop[4] = {0}, nnew[4] = {0};
    omp_set_num_threads(th);
    #pragma omp parallel for schedule(dynamic, 1024) reduction(+:nbase) reduction(+:nloop[:4], nnew[:4])
    for (long long wi = 0; wi < words; wi++) {
        int w[64]; long long x = wi; int off = 0;
        if (canon) { w[0] = 0; off = 1; }
        for (int i = off; i < m; i++) { w[i] = (int)(x % NL); x /= NL; }
        for (int sp = 1; sp < m; sp++) {
            G g; load(&g, w, sp, w + sp, m - sp);
            if (!returns(&g, 64L * m * m)) continue;
            nbase++;
            int a[CAP], b[CAP], ta[CAP], tb[CAP], na = sp, nb = m - sp;
            for (int i = 0; i < na; i++) a[i] = w[i];
            for (int i = 0; i < nb; i++) b[i] = w[sp + i];
            for (int e = 1; e <= 3; e++) {
                for (int i = 0; i < na; i++) { ta[2 * i] = a[i]; ta[2 * i + 1] = a[i] + 1; }
                for (int i = 0; i < nb; i++) { tb[2 * i] = b[i]; tb[2 * i + 1] = b[i] + 1; }
                na *= 2; nb *= 2;
                memcpy(a, ta, sizeof(int) * na); memcpy(b, tb, sizeof(int) * nb);
                G d; load(&d, a, na, b, nb);
                int t3; long lam = loop_runs(&d, 50000000L, 1 << e, &t3);
                if (!lam) continue;
                nloop[e]++;
                if (!t3) {
                    nnew[e]++;
                    if (list) {
                        char s1[64], s2[64], line[160];
                        for (int i = 0; i < sp; i++) s1[i] = (char)('A' + w[i]);
                        s1[sp] = 0;
                        for (int i = sp; i < m; i++) s2[i - sp] = (char)('A' + w[i]);
                        s2[m - sp] = 0;
                        snprintf(line, sizeof line, "NEW %d %d %s %s", e, m, s1, s2);
                        #pragma omp critical
                        { keep(line); }
                    }
                }
            }
        }
    }
    qsort(lines, nlines, sizeof(char *), cmp);
    for (long i = 0; i < nlines; i++) printf("%s\n", lines[i]);
    printf("m=%d letters=%d mode=%s: base positions %lld; doubled e=1,2,3 reach a tie-free loop: %lld %lld %lld; not of Theorem-3 type: %lld %lld %lld\n",
           m, NL, canon ? "canon" : "full", nbase, nloop[1], nloop[2], nloop[3], nnew[1], nnew[2], nnew[3]);
    return 0;
}
