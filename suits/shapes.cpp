// Aligned loops of real War on EVERY multiset at once, by trick shapes.
// A phase (both players hold h = N/2 cards, play exactly their h cards, the last flip ends a trick, and each wins
// h cards) depends on the values only through its SHAPE: which columns tie and who wins each trick. So we follow
// card SLOTS, not values: column i of a phase pairs slot A[i] with slot B[i]; a tie merges the two slots into one
// equal-value class, a decided column adds a strict order edge, and the winner takes the pile reversed (D-M's
// natural pickup: pile gets [low, high] per pair, [p1, p2] on a tie). After k phases the arrangement must carry
// the same values as the start (or the swapped start): slot A_k[i] ~ slot i, B_k[i] ~ slot h+i.
// A shape sequence is realisable iff no strict edge joins a class to itself, the strict edges have no cycle, and
// every class has at most 4 cards; values are then a linear extension of the class order. This is exact.
// Each solution is turned into values (1 + height in the class order) and checked again by playing the phase map.
// Exchanging the players and starting the orbit at another phase give the same loop; the search keeps one of each.
// usage: shapes N k [closure: 0 identity, 1 swap] [max solutions to print] [J j D file]
//   k = number of phases after which the deal must return (so loops of every period dividing k are found);
//   J j D file: work only on the subtrees at column D of phase 1 whose number is j mod J, one line per finished
//   subtree in file (finished subtrees are skipped on restart); run_parts.py runs the J parts side by side.
//   env SHAPES_CAP = most cards of one value (default 4); SHAPES_NOROT = keep every starting phase.
// build: g++ -O3 -mtune=native -o shapes shapes.cpp
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <vector>
#include <set>
#include <map>
#include <string>
#include <algorithm>

typedef unsigned long long u64;
static int N, H, K, SWAPCL, MAXPRINT, CAP = 4;          // CAP = most cards of one value (env SHAPES_CAP)
static int par[64]; static u64 msk[64];
static u64 gt[64];                                   // gt[s]: slots directly below slot s
struct Undo { int kind, a; u64 old; int b; };        // kind 0 union (a child, b root), 1 edge (gt[a] old)
static std::vector<Undo> st;
static long long nodes = 0, sols = 0, phase_done[64];
static std::map<std::pair<int, int>, long long> mixstat[64];   // per phase: (splits, straddles) among mixed pairs

static inline int find(int x) { while (par[x] != x) x = par[x]; return x; }
static inline bool below(int x, int y) {            // strict path from class(x) down to class(y)?
    u64 target = msk[find(y)], seen = msk[find(x)], fr = seen;
    while (fr) {
        u64 nx = 0;
        for (u64 f = fr; f; f &= f - 1) nx |= gt[__builtin_ctzll(f)];
        u64 ex = 0;
        for (u64 f = nx & ~seen; f; f &= f - 1) ex |= msk[find(__builtin_ctzll(f))];
        nx |= ex;
        if (nx & target) return true;
        nx &= ~seen; seen |= nx; fr = nx;
    }
    return false;
}
static inline bool can_tie(int a, int b) {
    int ra = find(a), rb = find(b);
    if (ra == rb) return true;
    if (__builtin_popcountll(msk[ra] | msk[rb]) > CAP) return false;
    return !below(a, b) && !below(b, a);
}
static inline void do_tie(int a, int b) {
    int ra = find(a), rb = find(b);
    if (ra == rb) { st.push_back({2, 0, 0, 0}); return; }
    if (__builtin_popcountll(msk[ra]) < __builtin_popcountll(msk[rb])) std::swap(ra, rb);
    st.push_back({0, rb, msk[ra], ra}); par[rb] = ra; msk[ra] |= msk[rb];
}
static inline bool can_gt(int a, int b) { return find(a) != find(b) && !below(b, a); }
static inline void do_gt(int a, int b) { st.push_back({1, a, gt[a], 0}); gt[a] |= 1ULL << b; }
static inline void undo() {
    Undo u = st.back(); st.pop_back();
    if (u.kind == 0) { par[u.a] = u.a; msk[u.b] = u.old; }
    else if (u.kind == 1) gt[u.a] = u.old;
}

// canonical values: value = 1 + height of the class (longest strict chain below it). Classes at one height are
// incomparable, so they never meet in a column, and every tie and strict comparison is kept: this labelling follows
// the same shape sequence, and it depends only on the structure (not on the starting phase or slot names).
static std::vector<int> heights(int &nclasses) {
    std::vector<int> hgt(N, -1); nclasses = 0;
    for (int s = 0; s < N; s++) if (find(s) == s) nclasses++;
    bool changed = true; for (int s = 0; s < N; s++) if (find(s) == s) hgt[s] = 0;
    while (changed) {                                         // longest-path relaxation (the order is acyclic)
        changed = false;
        for (int s = 0; s < N; s++) for (u64 g = gt[s]; g; g &= g - 1) {
            int hi = find(s), lo = find(__builtin_ctzll(g));
            if (hgt[hi] < hgt[lo] + 1) { hgt[hi] = hgt[lo] + 1; changed = true; }
        }
    }
    std::vector<int> val(N); for (int s = 0; s < N; s++) val[s] = hgt[find(s)] + 1;
    return val;
}

// direct check with values: the phase map, positional (flip i = P1[i] vs P2[i]), D-M natural pickup
static bool phase_vals(std::vector<int> &p1, std::vector<int> &p2) {
    std::vector<int> w1, w2, pile;
    for (int i = 0; i < H; i++) {
        int x = p1[i], y = p2[i];
        pile.push_back(std::min(x, y)); pile.push_back(std::max(x, y));
        if (x != y) { auto &w = x > y ? w1 : w2; for (int j = (int)pile.size() - 1; j >= 0; j--) w.push_back(pile[j]); pile.clear(); }
    }
    if (!pile.empty() || (int)w1.size() != H || (int)w2.size() != H) return false;
    p1 = w1; p2 = w2; return true;
}

struct Info { long long seqs; std::string sizes; };
static std::map<std::string, Info> found;            // canonical height-labelled deal -> info
static std::map<std::string, Info> *cur = &found;     // where solution() records (the current prefix in part mode)
static int PJ = 1, Pj = 0, PD = -1; static long long prefix_counter = 0; static std::set<long long> pdone;
static FILE *pout = 0;
static std::string hexs(const std::string &x) { static const char *d = "0123456789abcdef"; std::string o;
    for (unsigned char c : x) { o += d[c >> 4]; o += d[c & 15]; } return o; }

static void solution() {
    sols++;
    int ncl; std::vector<int> val = heights(ncl);
    std::vector<int> p1(val.begin(), val.begin() + H), p2(val.begin() + H, val.end());
    std::vector<int> q1 = p1, q2 = p2; bool ok = true;      // verify with values only: F^K = identity / swap
    for (int t = 0; t < K && ok; t++) ok = phase_vals(q1, q2);
    if (ok) ok = SWAPCL ? (q1 == p2 && q2 == p1) : (q1 == p1 && q2 == p2);
    if (!ok) { printf("VERIFY FAILED\n"); exit(1); }
    std::string best; std::vector<int> r1 = p1, r2 = p2;
    for (int t = 0; t < 2 * K; t++) {                         // least over the orbit's states and the swap
        std::string s1, s2;
        for (int x : r1) { s1 += (char)x; } s1 += '|'; for (int x : r2) { s1 += (char)x; }
        for (int x : r2) { s2 += (char)x; } s2 += '|'; for (int x : r1) { s2 += (char)x; }
        std::string m = std::min(s1, s2); if (best.empty() || m < best) best = m;
        if (!phase_vals(r1, r2)) break;
    }
    // forced classes by height: e.g. "1,1/4" = two singleton classes at height 0, one 4-card class at height 1
    std::map<int, std::vector<int>> lv;
    for (int s = 0; s < N; s++) if (find(s) == s) lv[val[s]].push_back(__builtin_popcountll(msk[s]));
    std::string sz; for (auto &q : lv) { std::sort(q.second.begin(), q.second.end()); if (!sz.empty()) sz += '/';
        for (size_t j = 0; j < q.second.size(); j++) { if (j) sz += ','; sz += std::to_string(q.second[j]); } }
    auto &f = (*cur)[best]; f.seqs++; if (f.sizes.empty() || sz < f.sizes) f.sizes = sz;
}

// in the last phase every card written to W1 / W2 must carry the value of the start slot it lands on
static inline bool close_new(const std::vector<int> &W, size_t from, int player) {
    for (size_t j = from; j < W.size(); j++) {
        int target = (player == 1) == (SWAPCL == 0) ? (int)j : H + (int)j;
        if (!can_tie(W[j], target)) return false;
        do_tie(W[j], target);
    }
    return true;
}

// orbit-rotation symmetry: every orbit is found from each of its phases; keep only starts whose phase-1 shape is
// lexicographically least among the orbit's phases (column codes tie 0 < player 1 1 < player 2 2). Compatible with the
// swap break: the least shape over all phases and their swaps starts with a player-1 trick.
static int ROT = 1; static int code0[64]; static bool eqs[64];
static inline bool rot_ok(int t, int i, int c) { return !ROT || t == 0 || !eqs[t] || c >= code0[i]; }
static int codes[64][64];
static inline bool rot_enter(int t, int i, int c) { codes[t][i] = c; bool e = eqs[t]; if (t == 0) code0[i] = c; else if (eqs[t] && c > code0[i]) eqs[t] = false; return e; }

// DFS over columns: phase t, column i, arrangement A/B, outputs W1/W2, current pile, flips won so far
static void dfs(int t, int i, std::vector<int> &A, std::vector<int> &B, std::vector<int> &W1, std::vector<int> &W2,
                std::vector<int> &pile, int f1, int f2, int tlen) {
    nodes++;
    if (t == 0 && i == PD && pout) {                    // part mode: this subtree is one prefix
        long long id = prefix_counter++;
        if (id % PJ != Pj || pdone.count(id)) return;
        long long n0 = nodes, s0 = sols; std::map<std::string, Info> mine; cur = &mine;
        int keep = PD; PD = -1;                             // explore the subtree normally
        dfs(t, i, A, B, W1, W2, pile, f1, f2, tlen);
        PD = keep; cur = &found;
        std::string line = "prefix " + std::to_string(id) + " " + std::to_string(nodes - n0) + " " + std::to_string(sols - s0);
        for (auto &q : mine) { line += " " + hexs(q.first) + ":" + std::to_string(q.second.seqs) + ":" + q.second.sizes;
            auto &g = found[q.first]; g.seqs += q.second.seqs; if (g.sizes.empty()) g.sizes = q.second.sizes; }
        fprintf(pout, "%s\n", line.c_str()); fflush(pout);
        return;
    }
    if (i == H) {                                       // phase complete (the last column was decided)
        if (f1 != H / 2 || f2 != H / 2) return;
        phase_done[t]++;
        {   // mixed flip pairs of this phase: owner = winner of the flip's trick; SPLIT = two one-flip tricks, else STRADDLE
            int owner[64], w = 0;
            for (int c = H - 1; c >= 0; c--) { if (codes[t][c]) w = codes[t][c]; owner[c] = w; }
            int sp = 0, sd = 0;
            for (int r = 0; 2 * r + 1 < H; r++) if (owner[2 * r] != owner[2 * r + 1]) {
                bool single = codes[t][2 * r] && codes[t][2 * r + 1] && (r == 0 || codes[t][2 * r - 1]);
                if (single) sp++; else sd++;
            }
            mixstat[t][{sp, sd}]++;
        }
        if (t + 1 == K) { solution(); return; }      // closure was applied card by card during the last phase
        std::vector<int> nA = W1, nB = W2, nW1, nW2, np;
        eqs[t + 1] = true;
        dfs(t + 1, 0, nA, nB, nW1, nW2, np, 0, 0, 0);
        return;
    }
    int a = A[i], b = B[i];
    // tie (never on the last column)
    if (i < H - 1 && rot_ok(t, i, 0) && can_tie(a, b)) {
        do_tie(a, b); pile.push_back(a); pile.push_back(b); bool sv = rot_enter(t, i, 0);
        dfs(t, i + 1, A, B, W1, W2, pile, f1, f2, tlen + 1);
        eqs[t] = sv; pile.pop_back(); pile.pop_back(); undo();
    }
    // player 1 wins the trick: pile gets [b, a], W1 takes the pile reversed
    if (f1 + tlen + 1 <= H / 2 && rot_ok(t, i, 1) && can_gt(a, b)) {
        size_t mark = st.size(); do_gt(a, b); size_t w = W1.size(), pn = pile.size();
        pile.push_back(b); pile.push_back(a);
        for (int j = (int)pile.size() - 1; j >= 0; j--) W1.push_back(pile[j]);
        std::vector<int> saved(pile.begin(), pile.end()); pile.clear();
        bool sv = rot_enter(t, i, 1);
        if (t + 1 < K || close_new(W1, w, 1)) dfs(t, i + 1, A, B, W1, W2, pile, f1 + tlen + 1, f2, 0);
        eqs[t] = sv;
        pile = saved; pile.resize(pn); W1.resize(w); while (st.size() > mark) undo();
    }
    // player 2 wins: pile gets [a, b]
    // (swap symmetry: in phase 1 the first trick goes to player 1; the swapped loop is the same loop)
    if (f2 + tlen + 1 <= H / 2 && !(t == 0 && f1 == 0 && f2 == 0) && rot_ok(t, i, 2) && can_gt(b, a)) {
        size_t mark = st.size(); do_gt(b, a); size_t w = W2.size(), pn = pile.size();
        pile.push_back(a); pile.push_back(b);
        for (int j = (int)pile.size() - 1; j >= 0; j--) W2.push_back(pile[j]);
        std::vector<int> saved(pile.begin(), pile.end()); pile.clear();
        bool sv = rot_enter(t, i, 2);
        if (t + 1 < K || close_new(W2, w, 2)) dfs(t, i + 1, A, B, W1, W2, pile, f1, f2 + tlen + 1, 0);
        eqs[t] = sv;
        pile = saved; pile.resize(pn); W2.resize(w); while (st.size() > mark) undo();
    }
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: shapes N k [closure] [max solutions to print] [J j D file]\n"); return 2; }
    N = atoi(argv[1]); H = N / 2; K = atoi(argv[2]); SWAPCL = argc > 3 ? atoi(argv[3]) : 0; MAXPRINT = argc > 4 ? atoi(argv[4]) : 20;
    // part mode: shapes N k closure maxprint J j D file -> prefixes (subtrees at column D of phase 1) with id % J == j,
    // one line per finished prefix in file; finished prefixes are skipped on restart
    if (getenv("SHAPES_NOROT")) ROT = 0;
    if (getenv("SHAPES_CAP")) CAP = atoi(getenv("SHAPES_CAP"));
    if (argc > 8) {
        PJ = atoi(argv[5]); Pj = atoi(argv[6]); PD = atoi(argv[7]);
        FILE *f = fopen(argv[8], "rb"); char line[1 << 16];
        if (f) { while (fgets(line, sizeof line, f)) { long long id; if (sscanf(line, "prefix %lld", &id) == 1) pdone.insert(id); } fclose(f); }
        pout = fopen(argv[8], "ab");
        fprintf(pout, "# start N=%d k=%d closure=%d part %d of %d, depth %d, already done %zu\n", N, K, SWAPCL, Pj, PJ, PD, pdone.size()); fflush(pout);
    }
    if (N > 64 || N % 2) { printf("N must be even and <= 64\n"); return 1; }
    for (int s = 0; s < N; s++) { par[s] = s; msk[s] = 1ULL << s; gt[s] = 0; }
    std::vector<int> A(H), B(H), W1, W2, pile;
    for (int i = 0; i < H; i++) { A[i] = i; B[i] = H + i; }
    dfs(0, 0, A, B, W1, W2, pile, 0, 0, 0);
    if (pout) { fprintf(pout, "# part finished, prefixes seen %lld\n", prefix_counter); fclose(pout); printf("PART DONE\n"); }
    printf("shapes N=%d k=%d closure=%s: %lld nodes, %lld shape sequences realisable, %zu distinct loops (orbit rotation and swap identified)\n",
           N, K, SWAPCL ? "swap" : "identity", nodes, sols, found.size());
    printf("  partial orbits reaching the end of phase 1..%d:", K);
    for (int t = 0; t < K; t++) printf(" %lld", phase_done[t]);
    printf("\n");
    for (int t = 0; t < K; t++) {
        printf("  phase %d completions by (splits, straddles):", t + 1); int c = 0;
        for (auto &q : mixstat[t]) { if (c++ < 12) printf(" (%d,%d):%lld", q.first.first, q.first.second, q.second); }
        printf(c > 12 ? " ...%c" : "%c", 10);
    }
    int shown = 0;
    for (auto &p : found) {
        if (shown++ >= MAXPRINT) break;
        printf("  forced classes by height %s; height-labelled deal:", p.second.sizes.c_str());
        for (char c : p.first) { if (c == '|') printf(" |"); else printf(" %d", (int)c); }
        printf("   [%lld sequences]\n", p.second.seqs);
    }
    return 0;
}
