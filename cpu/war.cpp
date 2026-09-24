// Count deals of an n-card War deck (ranks 0..n-1, all distinct) that never end.
// Deal: permutation p, player 1 (A) gets p[0],p[2],..., player 2 (B) gets p[1],p[3],... (A gets ceil(n/2)).
// Each turn: top cards compared, higher wins; winner puts both at bottom of own pile,
// order: mode 0 = winner's card first (Spivey), mode 1 = loser's card first.
// usage: war n mode      build: g++ -O3 -march=native -fopenmp -o war war.cpp
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <algorithm>
#include <vector>
#include <omp.h>
typedef unsigned long long u64;
struct S { u64 a, b; int la, lb; };
static int MODE;
static long long jobs_done = 0;
static inline bool ended(const S& s) { return s.la == 0 || s.lb == 0; }
static inline void step(S& s) {
    u64 ca = s.a & 15, cb = s.b & 15;
    s.a >>= 4; s.b >>= 4; s.la--; s.lb--;
    u64 w, l;
    if (ca > cb) { w = ca; l = cb; if (MODE == 0) { s.a |= w << (4*s.la); s.a |= l << (4*(s.la+1)); } else { s.a |= l << (4*s.la); s.a |= w << (4*(s.la+1)); } s.la += 2; }
    else { w = cb; l = ca; if (MODE == 0) { s.b |= w << (4*s.lb); s.b |= l << (4*(s.lb+1)); } else { s.b |= l << (4*s.lb); s.b |= w << (4*(s.lb+1)); } s.lb += 2; }
}
static inline bool eq(const S& x, const S& y) { return x.a == y.a && x.b == y.b && x.la == y.la; }
// returns -1 if cycles, else game length
static long long run(S s) {
    if (ended(s)) return 0;
    S tort = s; S hare = s; step(hare); long long t = 1;
    if (ended(hare)) return t;
    long long power = 1, lam = 1;
    while (!eq(tort, hare)) {
        if (power == lam) { tort = hare; power *= 2; lam = 0; }
        step(hare); t++; lam++;
        if (ended(hare)) return t;
    }
    return -1;
}
int main(int argc, char** argv) {
    int n = atoi(argv[1]); MODE = atoi(argv[2]);
    std::vector<std::pair<int,int>> jobs;
    for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) if (i != j) jobs.push_back({i, j});
    long long cyc = 0, total = 0, longest = 0;
    #pragma omp parallel for schedule(dynamic,1) reduction(+:cyc,total) reduction(max:longest)
    for (int J = 0; J < (int)jobs.size(); J++) {
        int p[16]; p[0] = jobs[J].first; p[1] = jobs[J].second;
        int k = 2; for (int c = 0; c < n; c++) if (c != p[0] && c != p[1]) p[k++] = c;
        do {
            S s; s.a = 0; s.b = 0; s.la = 0; s.lb = 0;
            for (int i = 0; i < n; i++) { if (i % 2 == 0) { s.a |= (u64)p[i] << (4*s.la); s.la++; } else { s.b |= (u64)p[i] << (4*s.lb); s.lb++; } }
            long long r = run(s);
            total++;
            if (r < 0) cyc++; else if (r > longest) longest = r;
        } while (std::next_permutation(p + 2, p + n));
        long long dn;
        #pragma omp atomic capture
        dn = ++jobs_done;
        fprintf(stderr, "job %lld/%d done\n", dn, (int)jobs.size()); fflush(stderr);
    }
    printf("n=%d mode=%d deals=%lld cycling=%lld longest_finite=%lld\n", n, MODE, total, cyc, longest);
    return 0;
}
