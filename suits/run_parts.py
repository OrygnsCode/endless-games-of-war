"""Run the J parts of a shapes.exe search side by side and wait for all of them.

Each part resumes from its own prefix file (finished prefixes are skipped), so this launcher can simply be
restarted after a crash. Prints ALL PARTS DONE only when every part printed PART DONE and exited 0.
usage: python run_parts.py EXE N k closure J D OUTPREFIX
  part j writes OUTPREFIX_j.txt and its stdout to OUTPREFIX_j.log
"""
import subprocess, sys

exe, n, k, closure, J, D, out = sys.argv[1:8]
procs = []
for j in range(int(J)):
    log = open('%s_%d.log' % (out, j), 'a')
    procs.append((subprocess.Popen([exe, n, k, closure, '0', J, str(j), D, '%s_%d.txt' % (out, j)],
                                   stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)), j))   # no desktop window
ok = True
for p, j in procs:
    r = p.wait()
    with open('%s_%d.log' % (out, j), errors='replace') as f:
        done = 'PART DONE' in f.read().split('# launch')[-1]
    print('part %d exit %d %s' % (j, r, 'done' if done else 'NOT done'), flush=True)
    ok = ok and r == 0 and done
if ok:
    print('ALL PARTS DONE', flush=True)
sys.exit(0 if ok else 1)
