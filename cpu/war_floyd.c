/* War deals that never end: Floyd tortoise-hare, circular byte buffers, deals enumerated as a
   permutation split into the first ceil(n/2) cards (player 1, A) and the rest (player 2, B). With a third
   argument s, player 1 gets the first s cards instead, so summing over s = 1..n-1 scans every position.
   usage: war_floyd n rule [s]   (rule 0 = winner card first (Spivey), 1 = loser card first)
   build: gcc -O3 -march=native -fopenmp -o war_floyd war_floyd.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define M 32
#define MK 31
typedef struct { unsigned char a[M], b[M]; int ha, ca, hb, cb; } S;
static int RULE;
static inline void step(S *s){
  unsigned char x = s->a[s->ha], y = s->b[s->hb];
  s->ha = (s->ha+1)&MK; s->ca--; s->hb = (s->hb+1)&MK; s->cb--;
  unsigned char w = x>y?x:y, l = x>y?y:x;
  unsigned char f = RULE? l: w, g = RULE? w: l;
  if (x>y){ s->a[(s->ha+s->ca)&MK]=f; s->a[(s->ha+s->ca+1)&MK]=g; s->ca+=2; }
  else    { s->b[(s->hb+s->cb)&MK]=f; s->b[(s->hb+s->cb+1)&MK]=g; s->cb+=2; }
}
static inline int term(const S *s){ return s->ca==0 || s->cb==0; }
static inline int eq(const S *s, const S *t){
  if (s->ca!=t->ca) return 0;
  for(int i=0;i<s->ca;i++) if (s->a[(s->ha+i)&MK]!=t->a[(t->ha+i)&MK]) return 0;
  for(int i=0;i<s->cb;i++) if (s->b[(s->hb+i)&MK]!=t->b[(t->hb+i)&MK]) return 0;
  return 1;
}
static int nextperm(unsigned char *p, int k){
  int i=k-2; while(i>=0 && p[i]>=p[i+1]) i--; if(i<0) return 0;
  int j=k-1; while(p[j]<=p[i]) j--; unsigned char t=p[i];p[i]=p[j];p[j]=t;
  for(int l=i+1,r=k-1;l<r;l++,r--){t=p[l];p[l]=p[r];p[r]=t;} return 1;
}
int main(int argc, char **argv){
  int n = atoi(argv[1]); RULE = atoi(argv[2]);
  int sA = (argc>3)? atoi(argv[3]) : (n+1)/2;
  long long cyc=0, tot=0; long long maxr=0;
  int npre = n*(n-1);
  if (n<2){ printf("n=%d cyc=0 tot=1 maxrounds=0\n",n); return 0; }
  #pragma omp parallel for schedule(dynamic,1) reduction(+:cyc,tot) reduction(max:maxr)
  for (int pre=0; pre<npre; pre++){
    int c0 = pre/(n-1)+1, r = pre%(n-1);
    int c1 = 0, k=0; for(int v=1; v<=n; v++){ if(v==c0) continue; if(k==r){c1=v;break;} k++; }
    unsigned char p[M]; p[0]=c0; p[1]=c1; int m=2;
    for(int v=1; v<=n; v++) if(v!=c0 && v!=c1) p[m++]=v;
    do {
      S s0; s0.ha=0; s0.hb=0; s0.ca=sA; s0.cb=n-sA;
      for(int i=0;i<sA;i++) s0.a[i]=p[i];
      for(int i=sA;i<n;i++) s0.b[i-sA]=p[i];
      S t=s0, h=s0; long long hs=0; int cycled=0;
      for(;;){
        step(&h); hs++; if(term(&h)) break;
        step(&h); hs++; if(term(&h)) break;
        step(&t);
        if (eq(&t,&h)){ cycled=1; break; }
      }
      tot++;
      if (cycled) cyc++; else if (hs>maxr) maxr=hs;
    } while (nextperm(p+2, n-2));
  }
  printf("sA=%d n=%d rule=%d cyc=%lld tot=%lld maxrounds=%lld\n", sA, n, RULE, cyc, tot, maxr);
  return 0;
}
