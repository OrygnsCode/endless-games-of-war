"""Count the deals of single-suit War that never end, on the GPU, for n <= 17.

Rule (Spivey 2010): cards 0..n-1 (0 lowest), deck positions 0,2,4,... to player 1 (top first),
1,3,5,... to player 2; each turn the higher top card wins and the winner puts the winning card,
then the losing card, under their own pile. a(n) = number of the n! deck orders whose game never ends.

Card n-1 is kept out of the packed piles, so n = 17 still fits in 4-bit cards. Card n-1 never loses, so it
never changes hands and its holder never runs out of cards. Each player's other cards are 4-bit nibbles in
one 64-bit word (card values 0..n-2 <= 15), and for the holder we track only the depth p of card n-1
inside the holder's full pile (0 = on top). A turn:
  * holder's top is card n-1 (p == 0): the holder wins; the opponent's top card c goes under the
    holder's pile, right after card n-1, so p becomes the holder's packed length before c is added;
  * otherwise both players play their top nibbles, the holder's p drops by one, and the winner
    appends (winner, loser) to its packed word.
The game ends only when the non-holder is out of cards. A never-ending game is detected with Brent's
algorithm on the full state (both words, both lengths, p); no step limit, no hashing.

  python war17.py 15 --nmin 5            # reproduces the known terms
  python war17.py 17 --out n17 [--resume] [--per 32]
"""
import argparse
import json
import math
import os
import time

import cupy as cp

KERNEL = r'''
typedef unsigned long long u64;

// one turn; returns 1 if the game ended (non-holder out of cards)
__device__ __forceinline__ int turn(u64 &wh, int &lh, u64 &wo, int &lo, int &p, int top)
{
    // wh/lh: holder's packed word/length (without card `top`), wo/lo: opponent's
    if (p == 0) {                                  // holder plays card n-1 and wins
        u64 c = wo & 15ULL; wo >>= 4; lo--;
        p = lh;                                    // card n-1 goes to the bottom, depth = packed length
        wh |= c << (4 * lh); lh++;                 // then the captured card, after it
        return lo == 0;
    }
    u64 h = wh & 15ULL; wh >>= 4; lh--; p--;
    u64 o = wo & 15ULL; wo >>= 4; lo--;
    if (h > o) { wh |= h << (4 * lh); lh++; wh |= o << (4 * lh); lh++; }
    else       { wo |= o << (4 * lo); lo++; wo |= h << (4 * lo); lo++; }
    return lo == 0;
}

// returns 1 if the game from this deal never ends; *len = turns played for ending games
__device__ __forceinline__ int deal_cycles(const unsigned char* a, int n, u64* len)
{
    u64 w1 = 0, w2 = 0; int l1 = 0, l2 = 0, holder = 0, p = 0;
    for (int i = 0; i < n; i++) {
        int pl = i & 1;
        if (a[i] == (unsigned char)(n - 1)) { holder = pl; p = pl ? l2 : l1; continue; }
        if (pl == 0) { w1 |= ((u64)a[i]) << (4 * l1); l1++; }
        else         { w2 |= ((u64)a[i]) << (4 * l2); l2++; }
    }
    u64 wh = holder ? w2 : w1, wo = holder ? w1 : w2;
    int lh = holder ? l2 : l1, lo = holder ? l1 : l2;
    if (lo == 0) { *len = 0; return 0; }            // n = 1
    // Brent on (wh, lh, wo, lo, p)
    u64 th = wh, to = wo; int tlh = lh, tp = p;
    u64 power = 1, lam = 0, rounds = 0;
    while (true) {
        rounds++;
        if (turn(wh, lh, wo, lo, p, n - 1)) { *len = rounds; return 0; }
        lam++;
        if (wh == th && wo == to && lh == tlh && p == tp) { *len = rounds; return 1; }
        if (lam == power) { th = wh; to = wo; tlh = lh; tp = p; power <<= 1; lam = 0; }
    }
}

__device__ __forceinline__ void next_perm(unsigned char* a, int n)
{
    int i = n - 2;
    while (i >= 0 && a[i] >= a[i + 1]) i--;
    if (i < 0) return;
    int j = n - 1;
    while (a[j] <= a[i]) j--;
    unsigned char t = a[i]; a[i] = a[j]; a[j] = t;
    for (int l = i + 1, r = n - 1; l < r; l++, r--) { t = a[l]; a[l] = a[r]; a[r] = t; }
}

extern "C" __global__ void war17(int n, u64 start, u64 total, int per, const u64* fact,
                                 u64* out_cyc, u64* out_done, u64* out_maxfin)
{
    u64 tid = (u64)blockIdx.x * blockDim.x + threadIdx.x;
    u64 idx = start + tid * (u64)per;
    if (idx >= total) return;
    u64 cnt = total - idx; if (cnt > (u64)per) cnt = (u64)per;
    unsigned char a[17];
    unsigned int avail = (1u << n) - 1u;
    u64 r = idx;
    for (int i = 0; i < n; i++) {
        u64 f = fact[n - 1 - i];
        int d = (int)(r / f); r -= (u64)d * f;
        unsigned int m = avail;
        for (int k = 0; k < d; k++) m &= m - 1u;
        int v = __ffs(m) - 1;
        a[i] = (unsigned char)v; avail &= ~(1u << v);
    }
    u64 cyc = 0, maxfin = 0;
    for (u64 k = 0; k < cnt; k++) {
        u64 len;
        if (deal_cycles(a, n, &len)) cyc++;
        else if (len > maxfin) maxfin = len;
        if (k + 1 < cnt) next_perm(a, n);
    }
    atomicAdd(out_cyc, cyc);
    atomicAdd(out_done, cnt);
    atomicMax(out_maxfin, maxfin);
}
'''

_f = None


def kernel():
    global _f
    if _f is None:
        _f = cp.RawModule(code=KERNEL, options=("-std=c++14",)).get_function("war17")
    return _f


def run(n, per=64, threads=256, batch_threads=1 << 16, out=None, resume=False, quiet=True):
    assert 1 <= n <= 17
    batch_threads = max(threads, (batch_threads // threads) * threads)   # no overlap between launches
    total = math.factorial(n)
    fact = cp.asarray([math.factorial(i) for i in range(18)], dtype=cp.uint64)
    cyc = cp.zeros(1, dtype=cp.uint64); done = cp.zeros(1, dtype=cp.uint64); mx = cp.zeros(1, dtype=cp.uint64)
    start = 0
    prog = (out + ".progress") if out else None
    if resume and prog and os.path.exists(prog):
        st = json.load(open(prog))
        assert st["n"] == n and st["per"] == per and st["batch_threads"] == batch_threads
        start = st["next_start"]; cyc[0] = st["cyc"]; done[0] = st["done"]; mx[0] = st["maxfin"]
    f = kernel()
    span = batch_threads * per
    t0 = time.time(); last = 0.0; slowest = 0.0
    while start < total:
        tl = time.time()
        nth = min(batch_threads, (total - start + per - 1) // per)
        f(((nth + threads - 1) // threads,), (threads,),
          (cp.int32(n), cp.uint64(start), cp.uint64(total), cp.int32(per), fact, cyc, done, mx))
        cp.cuda.Device().synchronize()
        slowest = max(slowest, time.time() - tl)
        start += span
        if prog and (time.time() - last >= 10 or start >= total):
            last = time.time()
            st = {"n": n, "per": per, "batch_threads": batch_threads, "next_start": min(start, total),
                  "total": total, "cyc": int(cyc[0]), "done": int(done[0]), "maxfin": int(mx[0]),
                  "elapsed_s": round(time.time() - t0, 1), "slowest_launch_s": round(slowest, 3),
                  "updated": time.strftime("%Y-%m-%d %H:%M:%S")}
            json.dump(st, open(prog + ".tmp", "w")); os.replace(prog + ".tmp", prog)
            if not quiet:
                print("%.4f%%  cyc=%d  %.0fs  slowest %.3fs" % (100 * min(start, total) / total, int(cyc[0]),
                                                              time.time() - t0, slowest), flush=True)
    return int(cyc[0]), int(done[0]), int(mx[0]), time.time() - t0, slowest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("nmax", type=int)
    ap.add_argument("--nmin", type=int)
    ap.add_argument("--per", type=int, default=64)
    ap.add_argument("--batch", type=int, default=1 << 16)
    ap.add_argument("--out"); ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    for n in range(a.nmin or a.nmax, a.nmax + 1):
        c, d, mx, el, sl = run(n, per=a.per, batch_threads=a.batch, out=a.out, resume=a.resume, quiet=a.out is None)
        assert d == math.factorial(n), (d, math.factorial(n))
        print("n=%d  a(n)=%d  of %d deals  longest finite=%d  %.1fs  slowest launch %.3fs" % (n, c, d, mx, el, sl),
              flush=True)
