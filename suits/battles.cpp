// Real War with C suits and V values, under the rules of Delahaye and Mathieu's bataille.py:
// each trick both players turn over their top card and the pair goes on the pile as [low, high];
// equal cards mean a battle: both stay on the pile and the players turn over the next cards
// (no face-down card). The winner of the trick takes the pile reversed ("naturelle": winning card,
// losing card, then the tied pairs latest first) or sorted high first ("optimisee"). If a hand runs
// out during a battle, the pile goes to nobody and the game ends (both empty = draw).
// A game cycles when the pair of hands at the start of a trick repeats (Brent's method).
// A deal is an order of the C*V cards, player 1 gets the first half. D-M count games up to
// exchanging the players: classes = (ordered + symmetric) / 2. With half=1 only deals with
// hand 1 <= hand 2 (lexicographic) are played, which gives the same classes in half the time.
// A cycle is ALIGNED (D-M) if from some state with equal hands both players turn over exactly their
// N/2 cards by the end of a trick, the hands are equal again, and so on around the lap. Aligned loops
// can be stacked into one loop: the blocks never meet, so they may even share values.
// usage (mode: 0 naturelle, 1 optimisee; half: 1 = play only hand 1 <= hand 2; P = prefix length of the chunks):
//   battles V C mode threads half [P lo hi]   every deal of V values x C suits; chunks lo..hi-1 (default all)
//   battles r V C mode threads samples seed   random deals
//   battles a V C mode threads half P [lo hi] aligned loops only (phase map), every deal
//   battles q V C mode threads samples seed   aligned loops only, random deals
//   battles A V C mode threads P file         as 'a' with half = 1, resumable: one line per finished chunk in file
//   battles F V C mode threads P file         as the plain mode with half = 1, resumable, one line per chunk
//   battles M N threads [file]                aligned loops on every multiset of N cards with at most 4 copies
// build: g++ -O3 -mtune=native -fopenmp -o battles battles.cpp  (not -march=native: MinGW-w64 does not align
//   the stack for AVX, and such a build can crash; all counters are long long, since long is 32-bit on Windows)
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <vector>
#include <set>
#include <string>
#include <map>
#include <algorithm>
#include <omp.h>

static int V, C, MODE, N, H;

static void need(int argc, int n, const char *usage) {      // too few arguments: say how to call it
    if (argc < n) { fprintf(stderr, "usage: battles %s\n", usage); exit(2); }
}

struct Hand { uint8_t c[128]; int h, n; };            // ring buffer, capacity 128
static inline int pop(Hand &x) { int v = x.c[x.h]; x.h = (x.h + 1) & 127; x.n--; return v; }
static inline void push(Hand &x, int v) { x.c[(x.h + x.n) & 127] = (uint8_t)v; x.n++; }

static inline int encode(const Hand &a, const Hand &b, uint8_t *out) {   // linear form for comparison
    int k = 0;
    out[k++] = (uint8_t)a.n;
    for (int i = 0; i < a.n; i++) out[k++] = a.c[(a.h + i) & 127];
    for (int i = 0; i < b.n; i++) out[k++] = b.c[(b.h + i) & 127];
    return k;
}

// one trick; returns the number of pairs turned over (more than 1 = a battle)
static inline int trick(Hand &a, Hand &b) {
    uint8_t pile[128]; int pn = 0, f = 0;
    while (a.n && b.n) {
        int x = pop(a), y = pop(b); f++;
        if (x > y) { pile[pn++] = (uint8_t)y; pile[pn++] = (uint8_t)x; }
        else       { pile[pn++] = (uint8_t)x; pile[pn++] = (uint8_t)y; }
        if (x != y) {
            Hand &w = (x > y) ? a : b;
            if (MODE == 0) { for (int i = pn - 1; i >= 0; i--) push(w, pile[i]); }
            else { std::sort(pile, pile + pn, [](uint8_t p, uint8_t q) { return p > q; }); for (int i = 0; i < pn; i++) push(w, pile[i]); }
            return f;
        }
    }
    return f;                                          // a hand ran out in a battle: the pile is gone
}

struct Cyc { long long lam, flips, battles; int aligned; long long phase, t0; };
struct Res { int kind; long long tricks, flips; long long lam; std::string key; };   // kind 0 end, 1 draw, 2 cycle

// a, b sit on a cycle of lam tricks: canonical key (least state over the lap, either orientation)
static std::string cycle_key(Hand a, Hand b, long long lam) {
    uint8_t cur[160]; std::string best;
    for (long long t = 0; t < lam; t++) {
        int k = encode(a, b, cur); std::string s1((char *)cur, k);
        int k2 = encode(b, a, cur); std::string s2((char *)cur, k2);
        std::string m = std::min(s1, s2);
        if (best.empty() || m < best) best = m;
        trick(a, b);
    }
    return best;
}

static Cyc cycle_info(Hand a, Hand b, long long lam) {
    std::vector<long long> F(2 * lam + 1); std::vector<char> eq(2 * lam + 1);
    long long battles = 0; F[0] = 0; eq[0] = a.n == b.n;
    for (long long t = 1; t <= 2 * lam; t++) { int f = trick(a, b); if (t <= lam && f > 1) battles++; F[t] = F[t - 1] + f; eq[t] = a.n == b.n; }
    Cyc r{lam, F[lam], battles, 0, 0, 0};
    if (F[lam] % H) return r;
    std::map<long long, long long> at; for (long long t = 0; t <= 2 * lam; t++) at[F[t]] = t;
    for (long long t0 = 0; t0 < lam && !r.aligned; t0++) {
        if (!eq[t0]) continue;
        bool ok = true; long long first = -1;
        for (long long j = 1; j * H <= F[lam] && ok; j++) {
            auto it = at.find(F[t0] + j * H);
            if (it == at.end() || !eq[it->second]) ok = false; else if (first < 0) first = it->second - t0;
        }
        if (ok) { r.aligned = 1; r.phase = first; r.t0 = t0; }
    }
    return r;
}

// print the distinct cycles: lap, battles, alignment; for an aligned one also the state it is aligned from
static void report_cycles(const std::map<std::string, long long> &keys, int maxshow) {
    int shown = 0; long long naligned = 0;
    for (auto &p : keys) {
        const std::string &s = p.first; int na = (uint8_t)s[0];
        Hand a, b; a.h = b.h = a.n = b.n = 0;
        for (int i = 0; i < na; i++) push(a, (uint8_t)s[1 + i]);
        for (int i = 1 + na; i < (int)s.size(); i++) push(b, (uint8_t)s[i]);
        long long lam = 0; { Hand x = a, y = b; uint8_t s0[160], c1[160]; int k0 = encode(x, y, s0);
            do { trick(x, y); lam++; } while (!(encode(x, y, c1) == k0 && memcmp(c1, s0, k0) == 0)); }
        Cyc ci = cycle_info(a, b, lam);
        naligned += ci.aligned;
        if (shown++ < maxshow || ci.aligned) {
            printf("   lap %lld tricks, %lld pairs turned, %lld battles, %s", ci.lam, ci.flips, ci.battles, ci.aligned ? "ALIGNED" : "not aligned");
            if (ci.aligned) printf(" (phase %lld tricks)", ci.phase);
            printf(", %lld deals; least state:", p.second);
            for (int i = 0; i < a.n; i++) { printf(" %d", a.c[(a.h + i) & 127]); } printf(" |");
            for (int i = 0; i < b.n; i++) { printf(" %d", b.c[(b.h + i) & 127]); } printf("\n");
            if (ci.aligned) {
                for (long long t = 0; t < ci.t0; t++) trick(a, b);
                printf("      aligned from:");
                for (int i = 0; i < a.n; i++) { printf(" %d", a.c[(a.h + i) & 127]); } printf(" |");
                for (int i = 0; i < b.n; i++) { printf(" %d", b.c[(b.h + i) & 127]); } printf("\n");
            }
        }
    }
    printf("  aligned cycles: %lld of %zu\n", naligned, keys.size());
}

static Res play(const uint8_t *deck) {
    Hand a, b; a.h = b.h = 0; a.n = b.n = 0;
    for (int i = 0; i < H; i++) push(a, deck[i]);
    for (int i = H; i < N; i++) push(b, deck[i]);
    uint8_t snap[160], cur[160]; int sk = encode(a, b, snap);
    long long power = 1, lam = 1, tricks = 0, flips = 0;
    while (true) {
        if (a.n == 0 || b.n == 0) return Res{(a.n == 0 && b.n == 0) ? 1 : 0, tricks, flips, 0, ""};
        flips += trick(a, b); tricks++;
        if (a.n == 0 || b.n == 0) return Res{(a.n == 0 && b.n == 0) ? 1 : 0, tricks, flips, 0, ""};
        int ck = encode(a, b, cur);
        if (ck == sk && memcmp(cur, snap, ck) == 0) return Res{2, tricks, flips, lam, cycle_key(a, b, lam)};
        if (power == lam) { memcpy(snap, cur, ck); sk = ck; power *= 2; lam = 0; }
        lam++;
    }
}

static void prefixes(int P, std::vector<int> &cnt, std::vector<uint8_t> &cur, std::vector<std::vector<uint8_t>> &out) {
    if ((int)cur.size() == P) { out.push_back(cur); return; }
    for (int v = 1; v <= V; v++) if (cnt[v]) { cnt[v]--; cur.push_back((uint8_t)v); prefixes(P, cnt, cur, out); cur.pop_back(); cnt[v]++; }
}

static inline uint64_t splitmix(uint64_t &x) {
    uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

// random deals: battles r V C mode threads samples seed
static int random_mode(int argc, char **argv) {
    need(argc, 8, "r V C mode threads samples seed");
    V = atoi(argv[2]); C = atoi(argv[3]); MODE = atoi(argv[4]); int th = atoi(argv[5]);
    long long samples = atoll(argv[6]); uint64_t seed = strtoull(argv[7], 0, 10);
    N = C * V; H = N / 2; omp_set_num_threads(th);
    long long cyc = 0, ends = 0, draws = 0; std::map<long long, long long> lens; std::map<std::string, long long> keys;
    #pragma omp parallel reduction(+:cyc,ends,draws)
    {
        uint64_t rng = seed * 1000003ULL + omp_get_thread_num() * 0x1234567ULL + 1;
        std::vector<uint8_t> deck(N); std::map<long long, long long> L; std::map<std::string, long long> K;
        #pragma omp for schedule(static)
        for (long long s = 0; s < samples; s++) {
            int k = 0; for (int v = 1; v <= V; v++) for (int j = 0; j < C; j++) deck[k++] = (uint8_t)v;
            for (int i = N - 1; i > 0; i--) { int j = (int)(splitmix(rng) % (uint64_t)(i + 1)); std::swap(deck[i], deck[j]); }
            Res r = play(deck.data());
            if (r.kind == 2) { cyc++; L[r.lam]++; K[r.key]++; } else if (r.kind == 1) draws++; else ends++;
        }
        #pragma omp critical
        { for (auto &p : L) lens[p.first] += p.second; for (auto &p : K) keys[p.first] += p.second; }
    }
    printf("random V=%d C=%d mode=%s samples=%lld seed=%llu: cycling %lld, ending %lld, draws %lld\n", V, C, MODE ? "optimisee" : "naturelle",
           samples, (unsigned long long)seed, cyc, ends, draws);
    printf("  cycle lengths in tricks (deals):");
    int sh = 0; for (auto &p : lens) if (sh++ < 60) printf(" %lld:%lld", p.first, p.second);
    printf("\n  distinct cycles up to swapping players: %zu\n", keys.size());
    report_cycles(keys, 10);
    return 0;
}

// Aligned loops are the periodic points of the PHASE MAP on deals: from equal hands of H cards, play whole
// tricks until each player has turned H cards; the phase succeeds when that happens exactly at the end of a
// trick with H cards in each hand again. Every state an aligned loop is aligned from is a deal, so testing
// every deal finds every aligned loop, and most deals fail within H pairs.
static inline bool phase(Hand &a, Hand &b) {
    long long f = 0;
    while (f < H) { if (a.n == 0 || b.n == 0) return false; f += trick(a, b); }
    return f == H && a.n == H && b.n == H;
}

struct PRes { int kind; long long p; std::string key; bool on; };      // kind 0 fails, 1 reaches a periodic orbit, 2 capped
static const long long PCAP = 1LL << 22;

static PRes phase_orbit(const uint8_t *deck) {
    Hand a, b; a.h = b.h = 0; a.n = b.n = 0;
    for (int i = 0; i < H; i++) push(a, deck[i]);
    for (int i = H; i < N; i++) push(b, deck[i]);
    uint8_t d0[160], snap[160], cur[160]; int k0 = encode(a, b, d0); memcpy(snap, d0, k0);
    long long power = 1, lam = 1, steps = 0;
    while (true) {
        if (!phase(a, b)) return PRes{0, 0, "", false};
        encode(a, b, cur);
        if (memcmp(cur, snap, k0) == 0) {          // a, b sit on an orbit of lam phases
            std::string best; bool on = false; Hand x = a, y = b;
            for (long long t = 0; t < lam; t++) {
                encode(x, y, cur); if (memcmp(cur, d0, k0) == 0) on = true;
                std::string s1((char *)cur, k0); encode(y, x, cur); std::string s2((char *)cur, k0);
                std::string m = std::min(s1, s2); if (best.empty() || m < best) best = m;
                phase(x, y);
            }
            return PRes{1, lam, best, on};
        }
        if (++steps > PCAP) return PRes{2, 0, "", false};
        if (power == lam) { memcpy(snap, cur, k0); power *= 2; lam = 0; }
        lam++;
    }
}

// orbit keys -> the game cycles they lie on (checked again with the full-play alignment test)
static void report_orbits(const std::map<std::string, long long> &orb) {
    std::map<std::string, long long> games; std::map<long long, long long> per;
    for (auto &p : orb) {
        const std::string &s = p.first; Hand a, b; a.h = b.h = a.n = b.n = 0;
        for (int i = 0; i < H; i++) push(a, (uint8_t)s[1 + i]);
        for (int i = 0; i < H; i++) push(b, (uint8_t)s[1 + H + i]);
        long long lam = 0; { Hand x = a, y = b; uint8_t s0[160], c1[160]; int k0 = encode(x, y, s0);
            do { trick(x, y); lam++; } while (!(encode(x, y, c1) == k0 && memcmp(c1, s0, k0) == 0) && lam < 100000000); }
        games[cycle_key(a, b, lam)] += p.second;
    }
    printf("  distinct phase orbits (up to swap) %zu, on %zu distinct game cycles\n", orb.size(), games.size());
    report_cycles(games, 40);
}

// battles a V C mode threads half P lo hi   (exhaustive over deals)
// battles q V C mode threads samples seed   (random deals)
static int aligned_mode(int argc, char **argv) {
    need(argc, 8, "a V C mode threads half P [lo hi]  |  q V C mode threads samples seed");
    bool rnd = argv[1][0] == 'q';
    V = atoi(argv[2]); C = atoi(argv[3]); MODE = atoi(argv[4]); int th = atoi(argv[5]);
    N = C * V; H = N / 2; omp_set_num_threads(th);
    long long tested = 0, reach = 0, periodic = 0, capped = 0; std::map<std::string, long long> orb;
    if (rnd) {
        long long samples = atoll(argv[6]); uint64_t seed = strtoull(argv[7], 0, 10);
        #pragma omp parallel reduction(+:tested,reach,periodic,capped)
        {
            uint64_t rng = seed * 1000003ULL + omp_get_thread_num() * 0x1234567ULL + 1;
            std::vector<uint8_t> deck(N); std::map<std::string, long long> K;
            #pragma omp for schedule(static)
            for (long long s = 0; s < samples; s++) {
                int k = 0; for (int v = 1; v <= V; v++) for (int j = 0; j < C; j++) deck[k++] = (uint8_t)v;
                for (int i = N - 1; i > 0; i--) { int j = (int)(splitmix(rng) % (uint64_t)(i + 1)); std::swap(deck[i], deck[j]); }
                tested++; PRes r = phase_orbit(deck.data());
                if (r.kind == 1) { reach++; periodic += r.on; K[r.key]++; } else if (r.kind == 2) capped++;
            }
            #pragma omp critical
            for (auto &p : K) orb[p.first] += p.second;
        }
        printf("aligned search, random V=%d C=%d mode=%s samples=%lld seed=%llu\n", V, C, MODE ? "optimisee" : "naturelle", samples, (unsigned long long)seed);
    } else {
        int half = atoi(argv[6]); int P = atoi(argv[7]);
        std::vector<int> cnt0(V + 1, C); cnt0[0] = 0; std::vector<uint8_t> cur; std::vector<std::vector<uint8_t>> pre;
        prefixes(P, cnt0, cur, pre);
        long long lo = argc > 8 ? atoll(argv[8]) : 0, hi = argc > 9 ? atoll(argv[9]) : (long long)pre.size();
        if (hi > (long long)pre.size()) hi = pre.size();
        #pragma omp parallel for schedule(dynamic, 1) reduction(+:tested,reach,periodic,capped)
        for (long long ci = lo; ci < hi; ci++) {
            std::vector<int> cnt(V + 1, C); cnt[0] = 0;
            std::vector<uint8_t> deck(N); for (int i = 0; i < P; i++) { deck[i] = pre[ci][i]; cnt[deck[i]]--; }
            int k = P; for (int v = 1; v <= V; v++) for (int j = 0; j < cnt[v]; j++) deck[k++] = (uint8_t)v;
            std::map<std::string, long long> K;
            do {
                if (half && memcmp(deck.data(), deck.data() + H, H) > 0) continue;
                tested++; PRes r = phase_orbit(deck.data());
                if (r.kind == 1) { reach++; periodic += r.on; K[r.key]++; } else if (r.kind == 2) capped++;
            } while (std::next_permutation(deck.begin() + P, deck.end()));
            #pragma omp critical
            for (auto &p : K) orb[p.first] += p.second;
        }
        printf("aligned search, exhaustive V=%d C=%d mode=%s half=%d chunks %lld..%lld of %zu (prefix %d)\n", V, C, MODE ? "optimisee" : "naturelle",
               half, lo, hi, pre.size(), P);
    }
    printf("  deals tested %lld; reach a periodic phase orbit %lld; periodic themselves %lld; capped at %lld phases %lld\n",
           tested, reach, periodic, PCAP, capped);
    report_orbits(orb);
    return 0;
}

static std::string hex(const std::string &s) {
    static const char *d = "0123456789abcdef"; std::string o;
    for (unsigned char c : s) { o += d[c >> 4]; o += d[c & 15]; }
    return o;
}
static std::string unhex(const char *p, int len) {
    std::string o; for (int i = 0; i + 1 < len; i += 2) { auto v = [](char c) { return c <= '9' ? c - '0' : c - 'a' + 10; };
        o += (char)(v(p[i]) * 16 + v(p[i + 1])); }
    return o;
}

// resumable exhaustive aligned search: battles A V C mode threads P file
// one line per finished chunk: "chunk ci tested reach periodic capped [orbitkey:count ...]"; done chunks are skipped
static int aligned_job(int argc, char **argv) {
    need(argc, 8, "A V C mode threads P file");
    V = atoi(argv[2]); C = atoi(argv[3]); MODE = atoi(argv[4]); int th = atoi(argv[5]); int P = atoi(argv[6]);
    const char *path = argv[7];
    N = C * V; H = N / 2; omp_set_num_threads(th);
    std::vector<int> cnt0(V + 1, C); cnt0[0] = 0; std::vector<uint8_t> cur; std::vector<std::vector<uint8_t>> pre;
    prefixes(P, cnt0, cur, pre);
    std::vector<char> done(pre.size(), 0); long long ndone = 0;
    { FILE *f = fopen(path, "rb"); char line[1 << 16];
      if (f) { while (fgets(line, sizeof line, f)) { long long ci; if (sscanf(line, "chunk %lld", &ci) == 1 && ci >= 0 && ci < (long long)pre.size() && !done[ci]) { done[ci] = 1; ndone++; } } fclose(f); } }
    FILE *out = fopen(path, "ab");
    fprintf(out, "# start V=%d C=%d mode=%d P=%d chunks=%zu already done=%lld threads=%d\n", V, C, MODE, P, pre.size(), ndone, th); fflush(out);
    printf("aligned job V=%d C=%d chunks %zu, done %lld, resuming\n", V, C, pre.size(), ndone); fflush(stdout);
    #pragma omp parallel for schedule(dynamic, 1)
    for (long long ci = 0; ci < (long long)pre.size(); ci++) {
        if (done[ci]) continue;
        std::vector<int> cnt(V + 1, C); cnt[0] = 0;
        std::vector<uint8_t> deck(N); for (int i = 0; i < P; i++) { deck[i] = pre[ci][i]; cnt[deck[i]]--; }
        int k = P; for (int v = 1; v <= V; v++) for (int j = 0; j < cnt[v]; j++) deck[k++] = (uint8_t)v;
        long long tested = 0, reach = 0, periodic = 0, capped = 0; std::map<std::string, long long> K;
        do {
            if (memcmp(deck.data(), deck.data() + H, H) > 0) continue;
            tested++; PRes r = phase_orbit(deck.data());
            if (r.kind == 1) { reach++; periodic += r.on; K[r.key]++; } else if (r.kind == 2) capped++;
        } while (std::next_permutation(deck.begin() + P, deck.end()));
        std::string line = "chunk " + std::to_string(ci) + " " + std::to_string(tested) + " " + std::to_string(reach) + " " +
                           std::to_string(periodic) + " " + std::to_string(capped);
        for (auto &p : K) line += " " + hex(p.first) + ":" + std::to_string(p.second);
        #pragma omp critical
        { fprintf(out, "%s\n", line.c_str()); fflush(out); }
    }
    fclose(out);
    // merge the whole file
    long long tested = 0, reach = 0, periodic = 0, capped = 0, chunks = 0; std::map<std::string, long long> orb; std::vector<char> seen(pre.size(), 0);
    FILE *f = fopen(path, "rb"); static char line[1 << 20];
    while (fgets(line, sizeof line, f)) {
        long long ci, t, r, p, c; int off = 0;
        if (sscanf(line, "chunk %lld %lld %lld %lld %lld%n", &ci, &t, &r, &p, &c, &off) != 5 || seen[ci]) continue;
        seen[ci] = 1; chunks++; tested += t; reach += r; periodic += p; capped += c;
        char *q = line + off;
        while (*q == ' ') { q++; char *colon = strchr(q, ':'); if (!colon) break; std::string key = unhex(q, (int)(colon - q));
            long long w = strtoll(colon + 1, &q, 10); orb[key] += w; }
    }
    fclose(f);
    printf("aligned job V=%d C=%d: chunks %lld of %zu; deals tested (swap-halved) %lld; reach a periodic phase orbit %lld; periodic %lld; capped %lld\n",
           V, C, chunks, pre.size(), tested, reach, periodic, capped);
    report_orbits(orb);
    if (chunks == (long long)pre.size()) printf("ALL CHUNKS DONE\n");
    return chunks == (long long)pre.size() ? 0 : 3;
}

// aligned loops on EVERY multiset of N cards with at most 4 copies of a value ('atoms'): War only compares,
// so a pattern (m1, ..., mk) = copies of the 1st, 2nd, ... smallest value covers every placement on k values.
// battles M N threads [file]
static void compositions(int left, std::vector<int> &cur, std::vector<std::vector<int>> &out) {
    if (left == 0) { out.push_back(cur); return; }
    for (int m = 1; m <= 4 && m <= left; m++) { cur.push_back(m); compositions(left - m, cur, out); cur.pop_back(); }
}

static int atom_mode(int argc, char **argv) {
    need(argc, 4, "M N threads [file]");
    // battles M N threads [file]: with a file, one line per finished pattern, finished patterns skipped on restart
    N = atoi(argv[2]); H = N / 2; int th = atoi(argv[3]); MODE = 0; omp_set_num_threads(th);
    const char *path = argc > 4 ? argv[4] : 0;
    std::vector<std::vector<int>> comps; std::vector<int> cur; compositions(N, cur, comps);
    std::vector<char> done(comps.size(), 0); long long ndone = 0;
    static char line[1 << 20];
    if (path) { FILE *f = fopen(path, "rb");
        if (f) { while (fgets(line, sizeof line, f)) { long long ci; if (sscanf(line, "pattern %lld", &ci) == 1 && ci >= 0 && ci < (long long)comps.size() && !done[ci]) { done[ci] = 1; ndone++; } } fclose(f); } }
    FILE *out = path ? fopen(path, "ab") : 0;
    if (out) { fprintf(out, "# start atoms N=%d patterns=%zu already done=%lld threads=%d\n", N, comps.size(), ndone, th); fflush(out); }
    long long tested = 0, hits = 0; std::vector<std::map<std::string, long long>> found(comps.size());
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:tested,hits)
    for (long long ci = 0; ci < (long long)comps.size(); ci++) {
        if (done[ci]) continue;
        std::vector<uint8_t> deck; for (int v = 0; v < (int)comps[ci].size(); v++) for (int j = 0; j < comps[ci][v]; j++) deck.push_back((uint8_t)(v + 1));
        long long t = 0, h = 0; std::map<std::string, long long> K;
        do {
            if (memcmp(deck.data(), deck.data() + H, H) > 0) continue;
            t++; PRes r = phase_orbit(deck.data());
            if (r.kind == 1) { h++; K[r.key]++; }
        } while (std::next_permutation(deck.begin(), deck.end()));
        tested += t; hits += h; found[ci] = K;
        if (out) {
            std::string l = "pattern " + std::to_string(ci) + " " + std::to_string(t) + " " + std::to_string(h);
            for (auto &p : K) l += " " + hex(p.first) + ":" + std::to_string(p.second);
            #pragma omp critical
            { fprintf(out, "%s\n", l.c_str()); fflush(out); }
        }
    }
    long long npat = comps.size() - ndone;
    if (path) {                                  // merge everything in the file
        fclose(out); tested = hits = 0; npat = 0; for (auto &m : found) m.clear();
        std::vector<char> seen(comps.size(), 0); FILE *f = fopen(path, "rb");
        while (fgets(line, sizeof line, f)) {
            long long ci, t, h; int off = 0;
            if (sscanf(line, "pattern %lld %lld %lld%n", &ci, &t, &h, &off) != 3 || seen[ci]) continue;
            seen[ci] = 1; npat++; tested += t; hits += h; char *q = line + off;
            while (*q == ' ') { q++; char *colon = strchr(q, ':'); if (!colon) break; std::string key = unhex(q, (int)(colon - q));
                long long w = strtoll(colon + 1, &q, 10); found[ci][key] += w; }
        }
        fclose(f);
    }
    printf("atoms N=%d: %lld of %zu patterns, %lld deals tested (swap-halved), %lld reach an aligned orbit\n", N, npat, comps.size(), tested, hits);
    for (size_t ci = 0; ci < comps.size(); ci++) if (!found[ci].empty()) {
        printf(" pattern (");
        for (size_t v = 0; v < comps[ci].size(); v++) printf("%s%d", v ? "," : "", comps[ci][v]);
        printf("):\n");
        report_orbits(found[ci]);
    }
    if (npat == (long long)comps.size()) printf("ALL PATTERNS DONE\n");
    return npat == (long long)comps.size() ? 0 : 3;
}

// resumable exhaustive FULL play (every cycle, not only aligned ones): battles F V C mode threads P file
// one line per finished chunk (swap-halved, weights as in the plain exhaustive mode):
// "chunk ci played sym cyc_ord cyc_sym end_ord dr_ord maxtr bestfl besttr bestdeck lens keys"
static int full_job(int argc, char **argv) {
    need(argc, 8, "F V C mode threads P file");
    V = atoi(argv[2]); C = atoi(argv[3]); MODE = atoi(argv[4]); int th = atoi(argv[5]); int P = atoi(argv[6]);
    const char *path = argv[7];
    N = C * V; H = N / 2; omp_set_num_threads(th);
    std::vector<int> cnt0(V + 1, C); cnt0[0] = 0; std::vector<uint8_t> cur; std::vector<std::vector<uint8_t>> pre;
    prefixes(P, cnt0, cur, pre);
    std::vector<char> done(pre.size(), 0); long long ndone = 0;
    static char line[1 << 22];
    { FILE *f = fopen(path, "rb");
      if (f) { while (fgets(line, sizeof line, f)) { long long ci; if (sscanf(line, "chunk %lld", &ci) == 1 && ci >= 0 && ci < (long long)pre.size() && !done[ci]) { done[ci] = 1; ndone++; } } fclose(f); } }
    FILE *out = fopen(path, "ab");
    fprintf(out, "# start full V=%d C=%d mode=%d P=%d chunks=%zu already done=%lld threads=%d\n", V, C, MODE, P, pre.size(), ndone, th); fflush(out);
    printf("full job V=%d C=%d chunks %zu, done %lld, resuming\n", V, C, pre.size(), ndone); fflush(stdout);
    #pragma omp parallel for schedule(dynamic, 1)
    for (long long ci = 0; ci < (long long)pre.size(); ci++) {
        if (done[ci]) continue;
        std::vector<int> cnt(V + 1, C); cnt[0] = 0;
        std::vector<uint8_t> deck(N); for (int i = 0; i < P; i++) { deck[i] = pre[ci][i]; cnt[deck[i]]--; }
        int k = P; for (int v = 1; v <= V; v++) for (int j = 0; j < cnt[v]; j++) deck[k++] = (uint8_t)v;
        long long played = 0, sym = 0, cyc = 0, cycs = 0, ends = 0, dr = 0, maxtr = 0, bf = -1, bt = -1;
        std::vector<uint8_t> bd(N); std::map<long long, long long> L; std::map<std::string, long long> K;
        do {
            int c = memcmp(deck.data(), deck.data() + H, H);
            if (c > 0) continue;
            long long w = c < 0 ? 2 : 1; played++; if (c == 0) sym++;
            Res r = play(deck.data());
            if (r.kind == 2) { cyc += w; if (c == 0) cycs++; L[r.lam] += w; K[r.key] += w; }
            else {
                if (r.kind == 1) dr += w; else ends += w;
                if (r.tricks > maxtr) maxtr = r.tricks;
                if (r.kind == 0 && (r.flips > bf || (r.flips == bf && r.tricks > bt))) { bf = r.flips; bt = r.tricks; bd = deck; }
            }
        } while (std::next_permutation(deck.begin() + P, deck.end()));
        std::string s = "chunk " + std::to_string(ci) + " " + std::to_string(played) + " " + std::to_string(sym) + " " + std::to_string(cyc) + " " +
                        std::to_string(cycs) + " " + std::to_string(ends) + " " + std::to_string(dr) + " " + std::to_string(maxtr) + " " +
                        std::to_string(bf) + " " + std::to_string(bt) + " " + hex(std::string(bd.begin(), bd.end())) + " L";
        for (auto &p : L) s += " " + std::to_string(p.first) + ":" + std::to_string(p.second);
        s += " K";
        for (auto &p : K) s += " " + hex(p.first) + ":" + std::to_string(p.second);
        #pragma omp critical
        { fprintf(out, "%s\n", s.c_str()); fflush(out); }
    }
    fclose(out);
    // merge
    long long chunks = 0, played = 0, sym = 0, cyc = 0, cycs = 0, ends = 0, dr = 0, maxtr = 0, bestfl = -1, besttr = -1;
    std::string bestdeck; std::map<long long, long long> lens; std::map<std::string, long long> keys; std::vector<char> seen(pre.size(), 0);
    FILE *f = fopen(path, "rb");
    while (fgets(line, sizeof line, f)) {
        long long ci, a1, a2, a3, a4, a5, a6, a7, a8, a9; char dk[512]; int off = 0;
        if (sscanf(line, "chunk %lld %lld %lld %lld %lld %lld %lld %lld %lld %lld %511s L%n", &ci, &a1, &a2, &a3, &a4, &a5, &a6, &a7, &a8, &a9, dk, &off) != 11 || seen[ci]) continue;
        seen[ci] = 1; chunks++; played += a1; sym += a2; cyc += a3; cycs += a4; ends += a5; dr += a6; if (a7 > maxtr) maxtr = a7;
        std::string d = unhex(dk, (int)strlen(dk));
        if (a8 > bestfl || (a8 == bestfl && a9 > besttr) || (a8 == bestfl && a9 == besttr && d < bestdeck)) { bestfl = a8; besttr = a9; bestdeck = d; }
        char *q = line + off; bool inK = false;
        while (*q == ' ') {
            q++; if (*q == 'K' && (q[1] == ' ' || q[1] == '\n' || q[1] == 0)) { inK = true; q++; continue; }
            char *colon = strchr(q, ':'); if (!colon) break;
            if (!inK) { long long len = strtoll(q, 0, 10); lens[len] += strtoll(colon + 1, &q, 10); }
            else { std::string key = unhex(q, (int)(colon - q)); keys[key] += strtoll(colon + 1, &q, 10); }
        }
    }
    fclose(f);
    long long tot = cyc + ends + dr;
    printf("full job V=%d C=%d: chunks %lld of %zu; plays %lld; ordered deals %lld, games up to swap %lld\n", V, C, chunks, pre.size(), played, tot, (tot + sym) / 2);
    printf("  cycling: ordered %lld, up to swap %lld   ending: %lld   draws: %lld\n", cyc, (cyc + cycs) / 2, ends, dr);
    printf("  longest game with a winner: %lld cards turned over in %lld tricks (most tricks in any finite game %lld)\n  deal:", bestfl, besttr, maxtr);
    for (int i = 0; i < (int)bestdeck.size(); i++) printf("%s%d", i == H ? " |" : " ", (uint8_t)bestdeck[i]);
    printf("\n  cycle lengths in tricks (ordered deals):");
    for (auto &p : lens) printf(" %lld:%lld", p.first, p.second);
    printf("\n  distinct cycles up to swapping players: %zu\n", keys.size());
    report_cycles(keys, 40);
    if (chunks == (long long)pre.size()) printf("ALL CHUNKS DONE\n");
    return chunks == (long long)pre.size() ? 0 : 3;
}

int main(int argc, char **argv) {
    if (argc > 1 && argv[1][0] == 'F') return full_job(argc, argv);
    if (argc > 1 && argv[1][0] == 'M') return atom_mode(argc, argv);
    if (argc > 1 && argv[1][0] == 'A') return aligned_job(argc, argv);
    if (argc > 1 && argv[1][0] == 'r') return random_mode(argc, argv);
    if (argc > 1 && (argv[1][0] == 'a' || argv[1][0] == 'q')) return aligned_mode(argc, argv);
    V = argc > 1 ? atoi(argv[1]) : 3; C = argc > 2 ? atoi(argv[2]) : 4;
    MODE = argc > 3 ? atoi(argv[3]) : 0; int th = argc > 4 ? atoi(argv[4]) : 8;
    int half = argc > 5 ? atoi(argv[5]) : 0; int P = argc > 6 ? atoi(argv[6]) : 2;
    N = C * V; H = N / 2; omp_set_num_threads(th);
    std::vector<int> cnt0(V + 1, C); cnt0[0] = 0; std::vector<uint8_t> cur; std::vector<std::vector<uint8_t>> pre;
    prefixes(P, cnt0, cur, pre);
    long long lo = argc > 7 ? atoll(argv[7]) : 0, hi = argc > 8 ? atoll(argv[8]) : (long long)pre.size();
    if (hi > (long long)pre.size()) hi = pre.size();
    long long played = 0, sym = 0, cyc_lt = 0, cyc_sym = 0, end_lt = 0, end_sym = 0, dr_lt = 0, dr_sym = 0, maxtr = 0;
    long long bestfl = -1, besttr = -1; std::vector<uint8_t> bestdeck(N);   // longest game with a winner, by cards turned over (D-M's record)
    std::map<long long, long long> lens; std::map<std::string, long long> keys;       // cycle length -> ordered deals; cycle -> ordered deals
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:played,sym,cyc_lt,cyc_sym,end_lt,end_sym,dr_lt,dr_sym) reduction(max:maxtr)
    for (long long ci = lo; ci < hi; ci++) {
        std::vector<int> cnt(V + 1, C); cnt[0] = 0;
        std::vector<uint8_t> deck(N); for (int i = 0; i < P; i++) { deck[i] = pre[ci][i]; cnt[deck[i]]--; }
        int k = P; for (int v = 1; v <= V; v++) for (int j = 0; j < cnt[v]; j++) deck[k++] = (uint8_t)v;
        std::map<long long, long long> L; std::map<std::string, long long> K; long long bf = -1, bt = -1; std::vector<uint8_t> bd(N);
        do {
            int c = memcmp(deck.data(), deck.data() + H, H);
            if (half && c > 0) continue;               // the swapped deal is played instead
            long long w = (half && c < 0) ? 2 : 1;          // ordered deals this play stands for
            played++; if (c == 0) sym++;
            Res r = play(deck.data());
            if (r.kind == 2) { if (c == 0) cyc_sym++; else cyc_lt += w; L[r.lam] += w; K[r.key] += w; }
            else {
                if (r.kind == 1) { if (c == 0) dr_sym++; else dr_lt += w; } else { if (c == 0) end_sym++; else end_lt += w; }
                if (r.tricks > maxtr) maxtr = r.tricks;
                if (r.kind == 0 && (r.flips > bf || (r.flips == bf && r.tricks > bt))) { bf = r.flips; bt = r.tricks; bd = deck; }
            }
        } while (std::next_permutation(deck.begin() + P, deck.end()));
        #pragma omp critical
        { for (auto &p : L) lens[p.first] += p.second; for (auto &p : K) keys[p.first] += p.second;
          if (bf > bestfl || (bf == bestfl && bt > besttr) || (bf == bestfl && bt == besttr && bd < bestdeck)) { bestfl = bf; besttr = bt; bestdeck = bd; } }
    }
    long long cyc = cyc_lt + cyc_sym, ends = end_lt + end_sym, draws = dr_lt + dr_sym, tot = cyc + ends + draws;
    printf("V=%d C=%d mode=%s chunks %lld..%lld of %zu (prefix %d) half=%d  plays=%lld\n", V, C, MODE ? "optimisee" : "naturelle",
           lo, hi, pre.size(), P, half, played);
    printf("  ordered deals=%lld symmetric=%lld games up to swap=%lld\n", tot, sym, (tot + sym) / 2);
    printf("  cycling: ordered %lld, up to swap %lld   ending: %lld   draws: %lld\n", cyc, (cyc + cyc_sym) / 2, ends, draws);
    printf("  longest game with a winner: %lld cards turned over in %lld tricks (most tricks in any finite game %lld)\n  deal:", bestfl, besttr, maxtr);
    for (int i = 0; i < N; i++) printf("%s%d", i == H ? " |" : " ", bestdeck[i]);
    printf("\n  cycle lengths in tricks (ordered deals):");
    for (auto &p : lens) printf(" %lld:%lld", p.first, p.second);
    printf("\n  distinct cycles up to swapping players: %zu\n", keys.size());
    report_cycles(keys, 40);
    return 0;
}
