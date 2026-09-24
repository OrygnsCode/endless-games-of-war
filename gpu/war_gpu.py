"""Count the deals of single-suit War that never end, on the GPU (n <= 16).

Cards are 0..n-1 here (0 lowest). Deck positions 0, 2, 4, ... go to player 1 and 1, 3, 5, ...
to player 2, top card first. Each turn the higher top card wins, and the winner puts the
winning card and then the losing card under their own pile (--rule 1 reverses the order).
The rule and the count are the same as in reference/war_ref.py.

Each GPU thread takes a run of consecutive deck orders (lexicographic rank), unranks the
first one, and steps through the rest with next_permutation. Both piles are packed as 4-bit
cards in 64-bit words, and a game that never ends is detected with Brent's cycle algorithm,
so there is no step limit and no hashing.

--half (even n): exchanging the players maps deals to deals and keeps a game endless, so
only the deals that give the highest card to player 1 are played and the count is doubled.

--canon scans the (n-1)! (n-1) positions in which player 1's top card is the highest card
instead of the deals. Up to exchanging the players every cycle passes through one of them.

Progress is written to <out>.progress every 10 seconds and at the end, and --resume continues from it.

  python war_gpu.py 12                        a(12)
  python war_gpu.py 15 --hist 128             a(15) and the cycle lengths
  python war_gpu.py 16 --canon --out n16c     every 16-card canonical position, resumable
"""
import argparse
import json
import math
import os
import sys
import time

import cupy as cp

KERNEL = r'''
typedef unsigned long long u64;
// one War turn on packed piles; rule 0: winner's card then loser's under the winner's pile (Spivey),
// rule 1: loser's card then winner's. Sets won1 = 1 if player 1 won the turn.
#define WAR_STEP(w1, l1, w2, l2, rule, won1) do { \
    u64 _c1 = (w1) & 15ULL; (w1) >>= 4; (l1)--; \
    u64 _c2 = (w2) & 15ULL; (w2) >>= 4; (l2)--; \
    if (_c1 > _c2) { u64 _a = (rule) ? _c2 : _c1, _b = (rule) ? _c1 : _c2; \
        (w1) |= _a << (4 * (l1)); (l1)++; (w1) |= _b << (4 * (l1)); (l1)++; (won1) = 1; } \
    else { u64 _a = (rule) ? _c1 : _c2, _b = (rule) ? _c2 : _c1; \
        (w2) |= _a << (4 * (l2)); (l2)++; (w2) |= _b << (4 * (l2)); (l2)++; (won1) = 0; } \
} while (0)

// After a loop is found, walk it once and record who wins each turn. Spivey's Theorem-3
// cycles have the players alternating in runs of exactly blk = 2^v turns (2^v = largest
// power of 2 dividing n). Returns 0 = that shape, 1 = some run has another length, 2 = loop
// longer than 512 turns (not checked).
__device__ __forceinline__ int loop_shape(u64 w1, int l1, u64 w2, int l2, u64 lam, int blk, int rule)
{
    if (lam > 512) return 2;
    u64 bits[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    for (u64 i = 0; i < lam; i++) {
        int won1;
        WAR_STEP(w1, l1, w2, l2, rule, won1);
        if (won1) bits[i >> 6] |= 1ULL << (i & 63);
    }
    int L = (int)lam;
    #define WB(i) ((int)((bits[((i) % L) >> 6] >> (((i) % L) & 63)) & 1ULL))
    int s = -1;
    for (int i = 0; i < L; i++) if (WB(i) != WB(i + L - 1)) { s = i; break; }
    if (s < 0) return 1;                      // one player wins every turn: not alternating
    int run = 1;
    for (int j = 1; j <= L; j++) {
        if (j < L && WB(s + j) == WB(s + j - 1)) { run++; continue; }
        if (run != blk) return 1;
        run = 1;
    }
    #undef WB
    return 0;
}

struct Meet { u64 w1, w2; int l1, l2; };

__device__ __forceinline__ bool war_sim(u64 w1, int l1, u64 w2, int l2, u64* rounds_out, u64* loop_out,
                                        Meet* meet, int rule)
{
    if (l1 == 0 || l2 == 0) { *rounds_out = 0; return false; }   // over before it starts
    // Brent: tortoise (t1,t2,tl), hare advances one turn at a time
    u64 t1 = w1, t2 = w2; int tl = l1;
    u64 power = 1, lam = 0, rounds = 0;
    while (true) {
        // one turn
        int won1;
        WAR_STEP(w1, l1, w2, l2, rule, won1);
        rounds++;
        if (l1 == 0 || l2 == 0) { *rounds_out = rounds; return false; }
        lam++;
        if (w1 == t1 && w2 == t2 && l1 == tl) { *rounds_out = rounds; *loop_out = lam;
            if (meet) { meet->w1 = w1; meet->w2 = w2; meet->l1 = l1; meet->l2 = l2; }
            return true; }
        if (lam == power) { t1 = w1; t2 = w2; tl = l1; power <<= 1; lam = 0; }
    }
}

__device__ __forceinline__ bool war_cycles(const unsigned char* p, int n, u64* rounds_out, u64* loop_out, int rule)
{
    // deal: deck positions 0,2,4,.. to player 1 (top first), 1,3,5,.. to player 2
    u64 w1 = 0, w2 = 0; int l1 = 0, l2 = 0;
    for (int i = 0; i < n; i++) {
        if ((i & 1) == 0) { w1 |= ((u64)p[i]) << (4 * l1); l1++; }
        else              { w2 |= ((u64)p[i]) << (4 * l2); l2++; }
    }
    return war_sim(w1, l1, w2, l2, rounds_out, loop_out, (Meet*)0, rule);
}

__device__ __forceinline__ bool next_perm(unsigned char* a, int n)
{
    int i = n - 2;
    while (i >= 0 && a[i] >= a[i + 1]) i--;
    if (i < 0) return false;
    int j = n - 1;
    while (a[j] <= a[i]) j--;
    unsigned char t = a[i]; a[i] = a[j]; a[j] = t;
    for (int l = i + 1, r = n - 1; l < r; l++, r--) { t = a[l]; a[l] = a[r]; a[r] = t; }
    return true;
}

extern "C" __global__ void war_count(int n, u64 start, u64 total, int per,
                                     const u64* fact, int half,
                                     u64* out_cyc, u64* out_done, u64* out_maxfin,
                                     u64* hist, int hbins)
{
    // per-block loop-length histogram in shared memory (bins 0..hbins-1, last bin = overflow)
    extern __shared__ unsigned int sh[];
    for (int b = threadIdx.x; b < hbins; b += blockDim.x) sh[b] = 0;
    if (hbins) __syncthreads();
    u64 tid = (u64)blockIdx.x * blockDim.x + threadIdx.x;
    u64 idx = start + tid * (u64)per;
    u64 cnt = 0;
    if (idx < total) { cnt = total - idx; if (cnt > (u64)per) cnt = (u64)per; }

    // unrank idx (lexicographic) into a permutation of 0..n-1
    unsigned char a[16];
    unsigned int avail = (1u << n) - 1u;
    u64 r = idx;
    for (int i = 0; i < n && cnt; i++) {
        u64 f = fact[n - 1 - i];
        int d = (int)(r / f); r -= (u64)d * f;
        unsigned int m = avail;
        for (int k = 0; k < d; k++) m &= m - 1u;      // drop d lowest set bits
        int v = __ffs(m) - 1;
        a[i] = (unsigned char)v; avail &= ~(1u << v);
    }
    int rule = (half >> 1) & 1; half &= 1;
    u64 cyc = 0, done = 0, maxfin = 0;
    for (u64 k = 0; k < cnt; k++) {
        bool take = true;
        if (half) {                                   // keep deals where card n-1 went to player 1
            int pos = 0; while (a[pos] != (unsigned char)(n - 1)) pos++;
            take = ((pos & 1) == 0);
        }
        if (take) {
            u64 rounds, loop = 0;
            if (war_cycles(a, n, &rounds, &loop, rule)) {
                cyc++;
                if (hbins) atomicAdd(&sh[loop < (u64)(hbins - 1) ? (int)loop : hbins - 1], 1u);
            }
            else if (rounds > maxfin) maxfin = rounds;
            done++;
        }
        if (k + 1 < cnt) next_perm(a, n);
    }
    if (cnt) {
        atomicAdd(out_cyc, cyc);
        atomicAdd(out_done, done);
        atomicMax(out_maxfin, maxfin);
    }
    if (hbins) {
        __syncthreads();
        for (int b = threadIdx.x; b < hbins; b += blockDim.x)
            if (sh[b]) atomicAdd(&hist[b], (u64)sh[b]);
    }
}

// Canonical positions: card n-1 (the highest) never changes hands and,
// in any endless game, keeps returning to the top of its holder's pile. Up to swapping the
// players, every cycle passes through a position whose player-1 top card is n-1.
// Enumerate: the other n-1 cards in every order q[0..n-2], and every split k = 0..n-2:
//   player 1 = [n-1, q[0..k-1]],  player 2 = [q[k..n-2]] (nonempty).  (n-1)! * (n-1) positions.
extern "C" __global__ void war_canon(int n, u64 start, u64 total, int per,
                                     const u64* fact, int blk,
                                     u64* out_cyc, u64* out_done, u64* out_maxfin,
                                     u64* hist, int hbins, u64* out_shape, int rule, u64* dhist, int dbins)
{
    extern __shared__ unsigned int sh[];
    for (int b = threadIdx.x; b < hbins; b += blockDim.x) sh[b] = 0;
    if (hbins) __syncthreads();
    int m = n - 1;
    u64 tid = (u64)blockIdx.x * blockDim.x + threadIdx.x;
    u64 idx = start + tid * (u64)per;
    u64 cnt = 0;
    if (idx < total) { cnt = total - idx; if (cnt > (u64)per) cnt = (u64)per; }
    unsigned char q[16];
    unsigned int avail = (1u << m) - 1u;
    u64 r = idx;
    for (int i = 0; i < m && cnt; i++) {
        u64 f = fact[m - 1 - i];
        int d = (int)(r / f); r -= (u64)d * f;
        unsigned int mm = avail;
        for (int k = 0; k < d; k++) mm &= mm - 1u;
        int v = __ffs(mm) - 1;
        q[i] = (unsigned char)v; avail &= ~(1u << v);
    }
    u64 cyc = 0, done = 0, maxfin = 0, nonstd = 0, unchk = 0;
    for (u64 it = 0; it < cnt; it++) {
        for (int k = 0; k <= m - 1; k++) {
            u64 w1 = (u64)(n - 1); int l1 = 1;
            for (int i = 0; i < k; i++) { w1 |= ((u64)q[i]) << (4 * l1); l1++; }
            u64 w2 = 0; int l2 = 0;
            for (int i = k; i < m; i++) { w2 |= ((u64)q[i]) << (4 * l2); l2++; }
            u64 rounds, loop = 0;
            Meet mt;
            if (war_sim(w1, l1, w2, l2, &rounds, &loop, &mt, rule)) {
                if (dbins) {
                    // Check whether the start lies on its cycle: walk lam turns and compare.
                    // On the way count cycle states whose player-1 top is card n-1 (c1) or whose player-2
                    // top is card n-1 (c2), and whether the player-swapped start lies on the cycle (sym).
                    // Every cycle orbit {C, swap C} contributes exactly d = (sym ? c1 : c1 + c2) enumerated
                    // on-cycle positions, so sum over d of dhist[d] / d = number of distinct cycles up to swap.
                    // Player 1 keeps card n-1 for good, so c2 and sym are always 0 here; they are kept as a check.
                    u64 v1 = w1, v2 = w2; int m1 = l1, m2 = l2; u64 c1n = 0, c2n = 0; int sym = 0;
                    for (u64 t = 0; t < loop; t++) {
                        if (m1 > 0 && (v1 & 15ULL) == (u64)(n - 1)) c1n++;
                        if (m2 > 0 && (v2 & 15ULL) == (u64)(n - 1)) c2n++;
                        if (v1 == w2 && v2 == w1 && m1 == l2) sym = 1;
                        int wn; WAR_STEP(v1, m1, v2, m2, rule, wn);
                    }
                    if (v1 == w1 && v2 == w2 && m1 == l1) {
                        u64 d = sym ? c1n : c1n + c2n;
                        atomicAdd(&dhist[d < (u64)(dbins - 1) ? d : (u64)(dbins - 1)], 1ULL);
                    }
                }
                cyc++;
                if (hbins) atomicAdd(&sh[loop < (u64)(hbins - 1) ? (int)loop : hbins - 1], 1u);
                if (blk) {
                    int shp = loop_shape(mt.w1, mt.l1, mt.w2, mt.l2, loop, blk, rule);
                    if (shp == 1) nonstd++;
                    else if (shp == 2) unchk++;
                }
            } else if (rounds > maxfin) maxfin = rounds;
            done++;
        }
        if (it + 1 < cnt) next_perm(q, m);
    }
    if (cnt) {
        atomicAdd(out_cyc, cyc);
        atomicAdd(out_done, done);
        atomicMax(out_maxfin, maxfin);
        if (blk) { atomicAdd(&out_shape[0], nonstd); atomicAdd(&out_shape[1], unchk); }
    }
    if (hbins) {
        __syncthreads();
        for (int b = threadIdx.x; b < hbins; b += blockDim.x)
            if (sh[b]) atomicAdd(&hist[b], (u64)sh[b]);
    }
}
'''

_mod = None


def kernel(name="war_count"):
    global _mod
    if _mod is None:
        _mod = cp.RawModule(code=KERNEL, options=("-std=c++14",))
    return _mod.get_function(name)


def run(n, half=False, per=256, threads=256, batch_threads=1 << 18, out=None, resume=False, quiet=False, hbins=0,
        canon=False, shape=False, rule=0, dbins=0):
    # canon: iterate over the (n-1)! orders of the other cards; each yields n-1 positions
    total = math.factorial(n - 1) if canon else math.factorial(n)
    if canon:   # each ordering yields n-1 positions: keep launches short (Windows GPU timeouts)
        batch_threads = max(1 << 12, batch_threads // max(1, n - 1))
    # A launch runs blocks*threads threads; if that exceeds batch_threads, the extra threads
    # would run into the next batch's range and count it twice; keep it an exact multiple.
    batch_threads = max(threads, (batch_threads // threads) * threads)
    fact = cp.asarray([math.factorial(i) for i in range(17)], dtype=cp.uint64)
    cyc = cp.zeros(1, dtype=cp.uint64)
    done = cp.zeros(1, dtype=cp.uint64)
    maxfin = cp.zeros(1, dtype=cp.uint64)
    hist = cp.zeros(max(hbins, 1), dtype=cp.uint64)
    shp = cp.zeros(2, dtype=cp.uint64)                 # [loops not of Theorem-3 shape, unchecked]
    dh = cp.zeros(max(dbins, 1), dtype=cp.uint64)      # distinct-cycle weights (canon only)
    if not canon:
        dbins = 0
    blk = (n & -n) if (canon and shape) else 0          # 2^v, the largest power of 2 dividing n
    if blk and os.environ.get("WAR_BLK_OVERRIDE"):      # negative control only: force a wrong block length
        blk = int(os.environ["WAR_BLK_OVERRIDE"])
    start = 0
    prog = (out + ".progress") if out else None
    if resume and prog and os.path.exists(prog):
        st = json.load(open(prog))
        assert st["n"] == n and st["half"] == half and st["per"] == per and st.get("canon", False) == canon
        start = st["next_start"]
        cyc[0] = st["cyc"]; done[0] = st["done"]; maxfin[0] = st["maxfin"]
        for k, v in st.get("hist", {}).items():
            hist[int(k)] = v
        if "shape" in st and st["shape"]:
            shp[0] = st["shape"][0]; shp[1] = st["shape"][1]
        for kk, vv in (st.get("dhist") or {}).items():
            dh[int(kk)] = vv
        assert st.get("rule", 0) == rule
        if not quiet:
            print("resuming at %d / %d" % (start, total), flush=True)
    f = kernel("war_canon" if canon else "war_count")
    span = batch_threads * per
    t0 = time.time()
    last_write = 0.0
    slowest = 0.0
    while start < total:
        tl = time.time()
        nthreads = min(batch_threads, (total - start + per - 1) // per)
        blocks = (nthreads + threads - 1) // threads
        if canon:
            args = (cp.int32(n), cp.uint64(start), cp.uint64(total), cp.int32(per),
                    fact, cp.int32(blk), cyc, done, maxfin, hist, cp.int32(hbins), shp,
                    cp.int32(rule), dh, cp.int32(dbins))
        else:
            args = (cp.int32(n), cp.uint64(start), cp.uint64(total), cp.int32(per),
                    fact, cp.int32((1 if half else 0) | (2 if rule else 0)), cyc, done, maxfin, hist, cp.int32(hbins))
        f((blocks,), (threads,), args, shared_mem=4 * hbins)
        cp.cuda.Device().synchronize()
        slowest = max(slowest, time.time() - tl)
        start += span
        if prog and (time.time() - last_write >= 10 or start >= total):
            last_write = time.time()
            st = {"n": n, "half": half, "canon": canon, "per": per, "next_start": min(start, total), "total": total,
                  "cyc": int(cyc[0]), "done": int(done[0]), "maxfin": int(maxfin[0]),
                  "hist": {str(i): int(v) for i, v in enumerate(cp.asnumpy(hist)) if v} if hbins else {},
                  "shape": [int(shp[0]), int(shp[1])] if blk else None,
                  "rule": rule,
                  "dhist": {str(i): int(v) for i, v in enumerate(cp.asnumpy(dh)) if v} if dbins else {},
                  "elapsed_s": round(time.time() - t0, 1), "slowest_launch_s": round(slowest, 3),
                  "updated": time.strftime("%Y-%m-%d %H:%M:%S")}
            tmp = prog + ".tmp"
            json.dump(st, open(tmp, "w"))
            os.replace(tmp, prog)
            if not quiet:
                frac = min(start, total) / total
                el = time.time() - t0
                print("%.4f%%  cyc=%d  elapsed %.0fs  slowest launch %.3fs" % (100 * frac, int(cyc[0]), el, slowest), flush=True)
    mult = 2 if half else 1
    c = int(cyc[0]) * mult
    d = int(done[0]) * mult
    h = {i: int(v) * mult for i, v in enumerate(cp.asnumpy(hist)) if v} if hbins else {}
    sh = (int(shp[0]), int(shp[1]), blk) if blk else None
    dd = {i: int(v) for i, v in enumerate(cp.asnumpy(dh)) if v} if dbins else None
    return c, d, int(maxfin[0]), time.time() - t0, h, sh, dd


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("nmax", type=int)
    ap.add_argument("--nmin", type=int, default=None)
    ap.add_argument("--half", action="store_true", help="even n: use player-swap symmetry")
    ap.add_argument("--per", type=int, default=256,
                    help="deck orders per thread per launch (with --canon: orders of the other n-1 cards, n-1 positions each)")
    ap.add_argument("--out", help="progress file prefix (enables resumable progress)")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--hist", type=int, default=0, help="loop-length histogram bins (last bin = overflow)")
    ap.add_argument("--canon", action="store_true",
                    help="scan canonical positions (player 1's top card is n) instead of deals")
    ap.add_argument("--rule", type=int, default=0, choices=[0, 1],
                    help="put-back order: 0 = winner's card first (Spivey), 1 = loser's card first")
    ap.add_argument("--distinct", action="store_true",
                    help="canon only: count distinct cycles up to swapping the players")
    ap.add_argument("--shape", action="store_true",
                    help="canon only: check every loop alternates in runs of exactly 2^v (Spivey Thm 3 type)")
    a = ap.parse_args()
    lo = a.nmin if a.nmin is not None else a.nmax
    for n in range(lo, a.nmax + 1):
        half = a.half and n % 2 == 0 and not a.canon
        c, d, mx, el, h, sh, dd = run(n, half=half, per=a.per, out=a.out, resume=a.resume,
                                      quiet=a.out is None, hbins=a.hist, canon=a.canon, shape=a.shape,
                                      rule=a.rule, dbins=4096 if a.distinct else 0)
        expect = math.factorial(n - 1) * (n - 1) if a.canon else math.factorial(n)
        assert d == expect, (d, expect)
        if h:
            assert sum(h.values()) == c, ("histogram does not add up", sum(h.values()), c)
        what = "canonical positions cycling" if a.canon else "a(n)"
        print("n=%d  %s=%d  of %d  longest finite=%d rounds  %.1fs%s"
              % (n, what, c, d, mx, el, "  (half)" if half else ""), flush=True)
        if dd is not None:
            bad = {k: v for k, v in dd.items() if v % k}
            assert not bad, ("distinct-cycle weights not divisible", bad)
            assert 4095 not in dd, "a cycle had more than 4094 canonical states: raise dbins"
            print("   distinct cycles (up to swapping players): %d   [on-cycle canonical positions by weight: %s]"
                  % (sum(v // k for k, v in dd.items()), dict(sorted(dd.items()))), flush=True)
        if sh:
            print("   loop shape: %d cycling positions checked for runs of exactly %d; "
                  "not that shape: %d; too long to check: %d" % (c, sh[2], sh[0], sh[1]), flush=True)
        if h:
            print("   loop lengths (rounds: %s): " % ("positions" if a.canon else "deals") + ", ".join(
                ("%s%d: %d" % (">=" if k == a.hist - 1 else "", k, v)) for k, v in sorted(h.items())), flush=True)
