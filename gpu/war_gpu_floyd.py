"""GPU count of the deals of single-suit War that never end: a second implementation, used to confirm war_gpu.py.

Rule (Spivey 2010): cards 1..n all distinct; each turn both players reveal their top card; the
higher card wins; the winner puts the winning card, then the losing card, at the bottom of their pile.
a(n) = number of the n! deals (player 1 = hand A = cards dealt at even positions, player 2 = hand B = odd positions)
whose game never ends.

Implementation choices:
- pile = u64 of 4-bit cards, top card in the highest occupied nibble, bottom at nibble 0;
- cycle detection: Floyd tortoise-hare;
- deals: Lehmer-code unranking of the first deal of each thread, then next_permutation (the same order as
  war_gpu.py);
- even n (--half): the highest card is placed at one of the n/2 positions of hand A and the other
  n-1 cards run over all (n-1)! orders; by player symmetry a(n) = 2 * (cycling count found);
- per-warp shuffle reduction, one atomicAdd per warp; many short launches (< 0.2 s each) because
  the operating system resets a display GPU whose kernels run longer than about 2 s.

Usage: python war_gpu_floyd.py n [--half] [--canon] [--q1 [--block B]] [--loser-first] [--chunk C] [--threads T] [--resume]
--q1 tests every loop for Spivey's Theorem-3 shape (the subject of his Question 1); the output field
q1_nonTheorem3_loops counts the cycling positions whose loop is not of that shape.
--loser-first plays the other order: the winner puts the losing card, then the winning card, at the bottom.
Progress and a resumable checkpoint go to war_gpu_floyd_n<N>[_half][_canon][_loser].progress / .ckpt next to this file.
"""
import sys, os, time, json, math, argparse
import cupy as cp

SRC = r'''
typedef unsigned long long u64;

__device__ __forceinline__ int pstep(u64 &a, u64 &b, int &la, int n) {
    int lb = n - la;
    u64 ta = (a >> (4 * (la - 1))) & 15ULL;
    u64 tb = (b >> (4 * (lb - 1))) & 15ULL;
    a &= (1ULL << (4 * (la - 1))) - 1ULL;
    b &= (1ULL << (4 * (lb - 1))) - 1ULL;
#if LOSER_FIRST
    if (ta > tb) { a = (a << 8) | (tb << 4) | ta; la += 1; return 1; }
    else         { b = (b << 8) | (ta << 4) | tb; la -= 1; return 0; }
#else
    if (ta > tb) { a = (a << 8) | (ta << 4) | tb; la += 1; return 1; }
    else         { b = (b << 8) | (tb << 4) | ta; la -= 1; return 0; }
#endif
}

extern "C" __global__ void war_count(int n, int mode, int pos, u64 start, u64 total, int chunk,
                                     u64 *out_cyc, u64 *out_max, u64 *out_deals,
                                     int q1, int L, u64 *out_bad) {
    // mode 0 = all n! deals; 1 = half (max card fixed at deal position pos, even n);
    // 2 = canon: player 1 (A) holds the max card on top plus q[0..pos-1], player 2 (B) holds q[pos..]
    int m = mode ? n - 1 : n;               // number of cards that are permuted
    u64 tid = (u64)blockIdx.x * blockDim.x + threadIdx.x;
    u64 first = start + tid * (u64)chunk;
    u64 cyc = 0, mx = 0, dealt = 0, bad = 0;
    if (first < total) {
        unsigned char q[16];
        // unrank `first` into q (lexicographic order of permutations of 0..m-1)
        {
            unsigned char avail[16];
            for (int i = 0; i < m; i++) avail[i] = (unsigned char)i;
            u64 f = 1; for (int i = 2; i < m; i++) f *= (u64)i;   // (m-1)!
            u64 r = first; int left = m;
            for (int i = 0; i < m; i++) {
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
            u64 a = 0, b = 0; int la = 0, lb = 0;
            if (mode == 2) {
                // canonical position: A = [max, q0..q(pos-1)] top first, B = [q(pos)..q(m-1)]
                a = (u64)(n - 1); la = 1;
                for (int i = 0; i < pos; i++) { a = (a << 4) | q[i]; la++; }
                for (int i = pos; i < m; i++) { b = (b << 4) | q[i]; lb++; }
            } else {
                // build the deal d[0..n-1]
                unsigned char d[16];
                if (mode == 1) {
                    int j = 0;
                    for (int i = 0; i < n; i++) d[i] = (i == pos) ? (unsigned char)(n - 1) : q[j++];
                } else {
                    for (int i = 0; i < n; i++) d[i] = q[i];
                }
                // hands: A = even positions, B = odd positions; first card dealt = top (highest nibble)
                for (int i = 0; i < n; i++) {
                    if ((i & 1) == 0) { a = (a << 4) | d[i]; la++; } else { b = (b << 4) | d[i]; lb++; }
                }
            }
            dealt++;
            if (la > 0 && lb > 0) {
                u64 ta = a, tb = b; int tla = la;          // tortoise
                u64 ha = a, hb = b; int hla = la;          // hare
                u64 steps = 0; int looped = 0;
                while (1) {
                    pstep(ha, hb, hla, n); steps++;
                    if (hla == 0 || hla == n) break;
                    pstep(ha, hb, hla, n); steps++;
                    if (hla == 0 || hla == n) break;
                    pstep(ta, tb, tla, n);
                    if (ta == ha && tb == hb && tla == hla) { looped = 1; break; }
                }
                if (looped) cyc++; else if (steps > mx) mx = steps;
                if (looped && q1) {
                    // Spivey Q1 test: around the loop, every maximal run of wins by one player has length L
                    u64 sa = ha, sb = hb; int sla = hla;
                    u64 ca = sa, cb = sb; int cla = sla;
                    int lam = 0, pw = -1, boundary = -1;
                    do {
                        int w = pstep(ca, cb, cla, n);
                        if (lam > 0 && w != pw && boundary < 0) boundary = lam;
                        pw = w; lam++;
                    } while (!(ca == sa && cb == sb && cla == sla));
                    int ok = 1;
                    if (boundary < 0) ok = 0;
                    else {
                        ca = sa; cb = sb; cla = sla;
                        for (int i = 0; i < boundary; i++) pstep(ca, cb, cla, n);
                        int run = 0; pw = -1;
                        for (int i = 0; i < lam; i++) {
                            int w = pstep(ca, cb, cla, n);
                            if (i == 0 || w == pw) run++;
                            else { if (run != L) ok = 0; run = 1; }
                            pw = w;
                        }
                        if (run != L) ok = 0;
                    }
                    if (!ok) bad++;
                }
            }
            // next permutation of q[0..m-1]
            {
                int i = m - 2;
                while (i >= 0 && q[i] >= q[i + 1]) i--;
                if (i >= 0) {
                    int j = m - 1;
                    while (q[j] <= q[i]) j--;
                    unsigned char t = q[i]; q[i] = q[j]; q[j] = t;
                    for (int l = i + 1, r2 = m - 1; l < r2; l++, r2--) { t = q[l]; q[l] = q[r2]; q[r2] = t; }
                }
            }
        }
    }
    // warp reductions
    for (int off = 16; off > 0; off >>= 1) {
        cyc   += __shfl_down_sync(0xffffffffu, cyc, off);
        dealt += __shfl_down_sync(0xffffffffu, dealt, off);
        bad   += __shfl_down_sync(0xffffffffu, bad, off);
        u64 o  = __shfl_down_sync(0xffffffffu, mx, off);
        if (o > mx) mx = o;
    }
    if ((threadIdx.x & 31) == 0) {
        if (cyc) atomicAdd(out_cyc, cyc);
        if (dealt) atomicAdd(out_deals, dealt);
        if (bad) atomicAdd(out_bad, bad);
        atomicMax(out_max, mx);
    }
}
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int)
    ap.add_argument('--half', action='store_true')
    ap.add_argument('--canon', action='store_true', help='scan the (n-1)! (n-1) positions in which player 1 has the highest card on top (every cycle passes through one, up to swapping the players)')
    ap.add_argument('--chunk', type=int, default=128)
    ap.add_argument('--threads', type=int, default=1 << 18)
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--q1', action='store_true', help='also test every loop for Spivey Theorem-3 block structure (runs of exactly 2^v wins)')
    ap.add_argument('--block', type=int, default=0, help='override block length (negative control)')
    ap.add_argument('--loser-first', action='store_true', help='the winner puts the losing card under first')
    args = ap.parse_args()
    n, half, canon = args.n, args.half, args.canon
    mode = 2 if canon else (1 if half else 0)
    if half and n % 2:
        sys.exit('--half needs even n')
    if args.q1 and args.loser_first:
        sys.exit('--q1 tests the shape of cycles under the winner-first rule only')
    here = os.path.dirname(os.path.abspath(__file__))
    tag = f"n{n}{'_half' if half else ''}{'_canon' if canon else ''}{'_loser' if args.loser_first else ''}"
    prog_path = os.path.join(here, f'war_gpu_floyd_{tag}.progress')
    ckpt_path = os.path.join(here, f'war_gpu_floyd_{tag}.ckpt')
    kern = cp.RawKernel(f"#define LOSER_FIRST {1 if args.loser_first else 0}\n" + SRC, 'war_count',
                        options=('-std=c++11',))
    m = n - 1 if mode else n
    total = math.factorial(m)
    positions = list(range(0, n - 1)) if canon else (list(range(0, n, 2)) if half else [0])
    state = {'pos_index': 0, 'start': 0, 'cyc': 0, 'max': 0, 'deals': 0}
    if args.resume and os.path.exists(ckpt_path):
        state = json.load(open(ckpt_path))
    out_cyc = cp.zeros(1, dtype=cp.uint64)
    out_max = cp.zeros(1, dtype=cp.uint64)
    out_deals = cp.zeros(1, dtype=cp.uint64)
    out_bad = cp.zeros(1, dtype=cp.uint64)
    out_bad[0] = state.get('bad', 0)
    Lblk = args.block if args.block else (n & -n)
    out_cyc[0] = state['cyc']; out_max[0] = state['max']; out_deals[0] = state['deals']
    T, C = args.threads, args.chunk
    block = 256
    # a full launch must be a whole number of blocks, otherwise the spare threads of the last block
    # would also process the start of the next launch's range
    assert T % block == 0, '--threads must be a multiple of 256'
    per_launch = T * C
    grand = total * len(positions)
    t0 = time.time(); last = t0; launches = 0
    pf = open(prog_path, 'a')
    for pi in range(state['pos_index'], len(positions)):
        pos = positions[pi]
        start = state['start'] if pi == state['pos_index'] else 0
        while start < total:
            nthreads = min(T, (total - start + C - 1) // C)
            grid = (nthreads + block - 1) // block
            kern((grid,), (block,), (cp.int32(n), cp.int32(mode), cp.int32(pos),
                  cp.uint64(start), cp.uint64(total), cp.int32(C), out_cyc, out_max, out_deals,
                  cp.int32(1 if args.q1 else 0), cp.int32(Lblk), out_bad))
            launches += 1
            start += nthreads * C
            now = time.time()
            if (launches % 64 == 0 and now - last > 10) or start >= total:
                cp.cuda.Device().synchronize()
                done = pi * total + start
                st = {'pos_index': pi, 'start': start, 'cyc': int(out_cyc[0]), 'max': int(out_max[0]),
                      'deals': int(out_deals[0]), 'bad': int(out_bad[0])}
                json.dump(st, open(ckpt_path, 'w'))
                rate = (done - (state['pos_index'] * total + state['start'])) / max(now - t0, 1e-9)
                pf.write(f"{time.strftime('%H:%M:%S')} n={n} half={half} pos={pos} done={done}/{grand} "
                         f"({100*done/grand:.3f}%) cyc_so_far={st['cyc']} max={st['max']} q1_bad={st['bad']} rate={rate:.3e}/s\n")
                pf.flush(); last = now
        state = {'pos_index': pi + 1, 'start': 0, 'cyc': int(out_cyc[0]), 'max': int(out_max[0]),
                 'deals': int(out_deals[0]), 'bad': int(out_bad[0])}
        json.dump(state, open(ckpt_path, 'w'))
    cp.cuda.Device().synchronize()
    cyc, mx, deals = int(out_cyc[0]), int(out_max[0]), int(out_deals[0])
    badc = int(out_bad[0])
    q1msg = f' q1_nonTheorem3_loops={badc} (block={Lblk})' if args.q1 else ''
    a = 2 * cyc if half else cyc
    expect_deals = grand
    rulemsg = ' rule=loser_first' if args.loser_first else ''
    if canon:
        msg = (f"n={n}{rulemsg} CANON positions_simulated={deals} (expected {expect_deals}) cycling_canonical_positions={cyc} "
               f"cycle_exists={'YES' if cyc else 'NO'}{q1msg} time={time.time()-t0:.1f}s")
    else:
        msg = (f"n={n}{rulemsg} half={half} deals_simulated={deals} (expected {expect_deals}) cycling_found={cyc} "
               f"a(n)={a} longest_finite={mx}{q1msg} time={time.time()-t0:.1f}s")
    print(msg, flush=True)
    pf.write(msg + '\n'); pf.close()
    if deals != expect_deals:
        print('ERROR: deal count mismatch', flush=True); sys.exit(1)

if __name__ == '__main__':
    main()
