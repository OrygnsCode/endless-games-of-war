"""GPU count of the deals of single-suit War that never end, for up to 20 cards.

A third GPU counter. It enumerates the deals in the same order as war_gpu_floyd.py, but the cards are
5 bits and a pile is two u64 words (lo, hi) holding up to 25 cards, top card in the lowest 5 bits, bottom
card at the highest occupied position. The piles have room for 24 cards, but deal ranks are 64-bit, so
n <= 20. Rule (Spivey 2010): the higher top card wins; the winning card, then the losing card, go under the
winner's pile. Deals: all n! orders, player 1 (A) gets the cards at even positions (first dealt on top).

Cycle detection, two independent methods:
  --det floyd   Floyd tortoise-hare (reference, any n).
  --det streak  (odd n only) Spivey Thm 6: in a cycle the players alternate winning forever, and while
                they alternate every card moves along a fixed track, so after
                lambda = lcm(n+1, W, Lo-1) alternating turns (W = the about-to-win player's pile size,
                even; Lo = the other's) every card is back where it started. So: anchor the state at a
                moment where the next winner holds an even number of cards, and if the players then
                alternate for lambda turns, compare with the anchor. Equal = cycle (an exact
                repetition, so a proof). Otherwise re-anchor. A game that ends is counted as ending.
                Games still undecided after the step cap are counted as undetermined; every run in
                data/ reports undetermined=0.

Usage: python war24.py n [--det floyd|streak] [--start S --count C] [--chunk 32] [--threads 131072] [--resume] [--tag T]
--tag adds a suffix to the names of the progress and checkpoint files.
"""
import sys, os, time, json, math, argparse
import cupy as cp

SRC = r'''
typedef unsigned long long u64;


__device__ __forceinline__ unsigned popc5(u64 &lo, u64 &hi) {       // remove and return the top card
    unsigned c = (unsigned)(lo & 31ULL);
    lo = (lo >> 5) | (hi << 59); hi >>= 5;
    return c;
}
__device__ __forceinline__ void put(u64 &lo, u64 &hi, int L, u64 v, int bits) { // write v (bits wide) at card index L
    int p = 5 * L;
    u64 slo = (p < 64) ? (v << p) : 0ULL;
    u64 shi = (p >= 64) ? (v << (p - 64)) : ((p + bits > 64) ? (v >> (64 - p)) : 0ULL);
    lo |= slo; hi |= shi;
}
__device__ __forceinline__ int pstep(u64 &alo, u64 &ahi, u64 &blo, u64 &bhi, int &la, int n) {
    int lb = n - la;
    unsigned ta = popc5(alo, ahi), tb = popc5(blo, bhi);
    if (ta > tb) { put(alo, ahi, la - 1, (u64)ta | ((u64)tb << 5), 10); la += 1; return 1; }
    else         { put(blo, bhi, lb - 1, (u64)tb | ((u64)ta << 5), 10); la -= 1; return 0; }
}
__device__ __forceinline__ unsigned peek(u64 lo) { return (unsigned)(lo & 31ULL); }
__device__ __forceinline__ int gcdi(int a, int b) { while (b) { int t = a % b; a = b; b = t; } return a; }
__device__ __forceinline__ int lcmi(int a, int b) { return a / gcdi(a, b) * b; }

extern "C" __global__ void war24_count(int n, int det, u64 start, u64 total, int chunk,
                                 u64 *out_cyc, u64 *out_max, u64 *out_deals, u64 *out_undet) {
    u64 tid = (u64)blockIdx.x * blockDim.x + threadIdx.x;
    u64 first = start + tid * (u64)chunk;
    u64 cyc = 0, mx = 0, dealt = 0, und = 0;
    const u64 CAP = 1ULL << 22;
    if (first < total) {
        unsigned char q[24];
        {   // Lehmer unrank `first` (lexicographic permutations of 0..n-1)
            unsigned char avail[24];
            for (int i = 0; i < n; i++) avail[i] = (unsigned char)i;
            u64 f = 1; for (int i = 2; i < n; i++) f *= (u64)i;
            u64 r = first; int left = n;
            for (int i = 0; i < n; i++) {
                u64 d = (left > 1) ? r / f : 0;
                if (left > 1) r %= f;
                q[i] = avail[d];
                for (int k = (int)d; k < left - 1; k++) avail[k] = avail[k + 1];
                left--;
                if (left > 1) f /= (u64)left;
            }
        }
        for (int c = 0; c < chunk; c++) {
            if (first + (u64)c >= total) break;
            // build piles card by card: the first card dealt is on top, at bit 0
            u64 alo = 0, ahi = 0, blo = 0, bhi = 0; int la = 0, lb = 0;
            for (int i = 0; i < n; i++) {
                u64 cd = q[i];
                if ((i & 1) == 0) { put(alo, ahi, la, cd, 5); la++; }
                else              { put(blo, bhi, lb, cd, 5); lb++; }
            }
            dealt++;
            u64 steps = 0; int result = 0;   // 0 ends, 1 cycle, 2 undetermined
            if (det == 0) {
                u64 tal = alo, tah = ahi, tbl = blo, tbh = bhi; int tla = la;
                u64 hal = alo, hah = ahi, hbl = blo, hbh = bhi; int hla = la;
                while (1) {
                    if (hla == 0 || hla == n) { result = 0; break; }
                    pstep(hal, hah, hbl, hbh, hla, n); steps++;
                    if (hla == 0 || hla == n) { result = 0; break; }
                    pstep(hal, hah, hbl, hbh, hla, n); steps++;
                    if (hla == 0 || hla == n) { result = 0; break; }
                    pstep(tal, tah, tbl, tbh, tla, n);
                    if (tal == hal && tah == hah && tbl == hbl && tbh == hbh && tla == hla) { result = 1; break; }
                    if (steps > CAP) { result = 2; break; }
                }
            } else {
                int anch = 0, lam = 0, since = 0, prevw = -1;
                u64 sal = 0, sah = 0, sbl = 0, sbh = 0; int sla = 0;
                while (1) {
                    if (la == 0 || la == n) { result = 0; break; }
                    if (steps > CAP) { result = 2; break; }
                    if (!anch) {
                        unsigned ta = peek(alo), tb = peek(blo);
                        int ws = (ta > tb) ? la : (n - la), ls = n - ws;
                        if ((ws & 1) == 0 && ls >= 2) {
                            anch = 1; since = 0; prevw = -1;
                            lam = lcmi(n + 1, lcmi(ws, ls - 1));
                            sal = alo; sah = ahi; sbl = blo; sbh = bhi; sla = la;
                        }
                    }
                    int w = pstep(alo, ahi, blo, bhi, la, n); steps++;
                    if (anch) {
                        if (w == prevw) { anch = 0; }
                        else {
                            prevw = w; since++;
                            if (since == lam) {
                                if (alo == sal && ahi == sah && blo == sbl && bhi == sbh && la == sla) { result = 1; break; }
                                anch = 0;
                            }
                        }
                    }
                }
            }
            if (result == 1) cyc++;
            else if (result == 2) und++;
            else if (steps > mx) mx = steps;
            // next permutation
            {
                int i = n - 2;
                while (i >= 0 && q[i] >= q[i + 1]) i--;
                if (i >= 0) {
                    int j = n - 1;
                    while (q[j] <= q[i]) j--;
                    unsigned char t = q[i]; q[i] = q[j]; q[j] = t;
                    for (int l = i + 1, r2 = n - 1; l < r2; l++, r2--) { t = q[l]; q[l] = q[r2]; q[r2] = t; }
                }
            }
        }
    }
    for (int off = 16; off > 0; off >>= 1) {
        cyc   += __shfl_down_sync(0xffffffffu, cyc, off);
        dealt += __shfl_down_sync(0xffffffffu, dealt, off);
        und   += __shfl_down_sync(0xffffffffu, und, off);
        u64 o  = __shfl_down_sync(0xffffffffu, mx, off);
        if (o > mx) mx = o;
    }
    if ((threadIdx.x & 31) == 0) {
        if (cyc) atomicAdd(out_cyc, cyc);
        if (dealt) atomicAdd(out_deals, dealt);
        if (und) atomicAdd(out_undet, und);
        atomicMax(out_max, mx);
    }
}
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int)
    ap.add_argument('--det', choices=['floyd', 'streak'], default='streak')
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--count', type=int, default=0, help='number of deals from --start (0 = to the end)')
    ap.add_argument('--chunk', type=int, default=32)
    ap.add_argument('--threads', type=int, default=1 << 17)
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--tag', default='', help='suffix for the progress and checkpoint file names')
    args = ap.parse_args()
    n = args.n
    assert 2 <= n <= 20, 'deal ranks are 64-bit: n <= 20'
    if args.det == 'streak' and n % 2 == 0:
        sys.exit('streak detection is only valid for odd n (Spivey Thm 6)')
    T, C, block = args.threads, args.chunk, 256
    assert T % block == 0, '--threads must be a multiple of 256'
    total_all = math.factorial(n)
    lo = args.start; hi = total_all if args.count == 0 else min(total_all, lo + args.count)
    here = os.path.dirname(os.path.abspath(__file__))
    tag = f"n{n}_{args.det}_{lo}_{hi}{args.tag}"
    prog = os.path.join(here, f'war24_{tag}.progress'); ckpt = os.path.join(here, f'war24_{tag}.ckpt')
    st = {'pos': lo, 'cyc': 0, 'max': 0, 'deals': 0, 'und': 0}
    if args.resume and os.path.exists(ckpt): st = json.load(open(ckpt))
    kern = cp.RawKernel(SRC, 'war24_count', options=('-std=c++17',))
    oc, om, od, ou = (cp.zeros(1, dtype=cp.uint64) for _ in range(4))
    oc[0] = st['cyc']; om[0] = st['max']; od[0] = st['deals']; ou[0] = st['und']
    det = 0 if args.det == 'floyd' else 1
    pos = st['pos']; t0 = time.time(); last = t0; launches = 0; pos0 = pos
    pf = open(prog, 'a')
    while pos < hi:
        nth = min(T, (hi - pos + C - 1) // C)
        grid = (nth + block - 1) // block
        kern((grid,), (block,), (cp.int32(n), cp.int32(det), cp.uint64(pos), cp.uint64(hi), cp.int32(C), oc, om, od, ou))
        pos += nth * C; launches += 1
        now = time.time()
        if (launches % 32 == 0 and now - last > 10) or pos >= hi:
            cp.cuda.Device().synchronize()
            st = {'pos': min(pos, hi), 'cyc': int(oc[0]), 'max': int(om[0]), 'deals': int(od[0]), 'und': int(ou[0])}
            json.dump(st, open(ckpt, 'w'))
            rate = (min(pos, hi) - pos0) / max(now - t0, 1e-9)
            pf.write(f"{time.strftime('%H:%M:%S')} n={n} det={args.det} pos={min(pos,hi)}/{hi} "
                     f"({100*(min(pos,hi)-lo)/(hi-lo):.4f}%) cyc={st['cyc']} max={st['max']} und={st['und']} rate={rate:.3e}/s\n")
            pf.flush(); last = now
    cp.cuda.Device().synchronize()
    cyc, mx, deals, und = int(oc[0]), int(om[0]), int(od[0]), int(ou[0])
    msg = (f"n={n} det={args.det} range=[{lo},{hi}) deals_simulated={deals} (expected {hi-lo}) "
           f"cycling={cyc} longest_finite={mx} undetermined={und} time={time.time()-t0:.1f}s")
    print(msg, flush=True); pf.write(msg + '\n'); pf.close()
    if deals != hi - lo: print('ERROR: deal count mismatch', flush=True); sys.exit(1)

if __name__ == '__main__':
    main()
