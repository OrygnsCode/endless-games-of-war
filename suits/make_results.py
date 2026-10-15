"""Write RESULTS.txt: the command and the output of every search in this directory.

Run from this directory after building the two programs:
    g++ -O3 -mtune=native -fopenmp -o battles battles.cpp
    g++ -O3 -mtune=native -o shapes shapes.cpp
    python make_results.py
The short searches are run again. For the long ones the result files in data/ are given to the same program,
on a temporary copy: it finds every chunk finished and prints the merged result. The last block is the recorded
output of the checks run in Delahaye and Mathieu's own program (checks/dm_crosscheck.txt), which is not included.
Each block is run with bash (Git Bash on Windows)."""
import hashlib, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))


def find_bash():
    """bash to run the blocks with; on Windows Git Bash, never the bash in System32 (that one starts WSL)"""
    if os.environ.get('BASH_EXE'):
        return os.environ['BASH_EXE']
    b = shutil.which('bash')
    if os.name != 'nt' or (b and 'system32' not in b.lower()):
        return b
    for root in [os.environ.get('ProgramFiles', ''), os.environ.get('ProgramW6432', '')]:
        for sub in [('Git', 'bin', 'bash.exe'), ('Git', 'usr', 'bin', 'bash.exe')]:
            c = os.path.join(root, *sub)
            if root and os.path.exists(c):
                return c
    sys.exit('Git Bash not found: set BASH_EXE to its bash.exe')


BASH = find_bash()
TMP = tempfile.mkdtemp().replace('\\', '/')
EXE = '.exe' if os.name == 'nt' else ''


def copy_then(src, cmd):
    """run cmd on a temporary copy of a result file, so the shipped file is not appended to"""
    dst = TMP + '/' + os.path.basename(src)
    return 'cp %s %s && %s' % (src, dst, cmd.replace('FILE', dst))


BLOCKS = [
    ('Compiler', 'g++ --version | head -1'),
    ('Every deal of V = 2, 3, 4 values in 4 suits, swap-halved. Delahaye and Mathieu (records_C4_naturelle.py) list: 38, 17,370'
     ' and 31,532,760 games; 0, 360 and 8545 that never end; one cycle of 19 tricks (not aligned) and 4 of 24 (aligned);'
     ' longest games with a winner 4, 37 and 142 tricks (8, 54 and 192 cards)',
     'for v in 2 3 4; do ./battles $v 4 0 4 1; done'),
    ('V = 4 without the halving gives the same classes', './battles 4 4 0 4 0 | sed -n 1,3p'),
    ('One suit, 10 cards: the deals that never end are A400411(10) = 395,940', './battles 10 1 0 4 1 | sed -n 1,3p'),
    ('Aligned loops on every multiset of N = 2..10 cards with at most 4 copies of a value, every deal', 'for n in 2 4 6 8 10; do ./battles M $n 4; done'),
    ('The same for N = 12 (1,490 count patterns): the merged result file', copy_then('data/atoms12.patterns', './battles M 12 4 FILE')),
    ('The shape search, exact over every multiset with at most 4 copies of a value: 8 cards (one structure, period 4),'
     ' 12 cards (none), 16 cards (period 4: the 4 stacks of two 8-card atoms; periods 3 and 5: none)',
     'for k in 1 2 4 8; do ./shapes 8 $k 0 3 | grep -v "^  phase"; done; ./shapes 8 2 1 3 | grep -v "^  phase";'
     ' for k in 1 2 3 4 8; do ./shapes 12 $k 0 3 | grep -v "^  phase"; done;'
     ' for k in 3 4 5; do ./shapes 16 $k 0 8 | grep -v "^  phase"; done'),
    ('Shape search, 20 cards, phase periods 1, 2, 3 (and 2 with the players exchanged)',
     'for k in 1 2 3; do ./shapes 20 $k 0 3 | grep -v "^  phase"; done; ./shapes 20 2 1 3 | grep -v "^  phase"'),
    ('Shape search, 20 cards, phase periods 4 and 5, run in 4 parts (python run_parts.py ./shapes 20 k 0 4 8 data/shapes20_periodk);'
     ' totals over the part files, each subtree counted once',
     "for k in 4 5; do cat data/shapes20_period${k}_?.txt | awk -v k=$k '/^prefix/ {if ($2 in s) d++; else {s[$2]=1; c++; n+=$3; q+=$4}} /prefixes seen/ {p=$NF}"
     " END {printf \"period %d: subtrees %d of %d, repeated %d, nodes %.0f, realisable shape sequences %d\\n\", k, c, p, d, n, q}'; done"),
    ('Without the 4-copy limit (SHAPES_CAP) aligned loops exist at 8, 12 and 20 cards, each with 5 or more copies of a value',
     'SHAPES_CAP=8 ./shapes 8 1 0 3 | grep -v "^  phase"; for k in 2 4; do SHAPES_CAP=12 ./shapes 12 $k 0 3 | grep -v "^  phase"; done;'
     ' for k in 1 2 3; do SHAPES_CAP=20 ./shapes 20 $k 0 3 | grep -v "^  phase"; done'),
    ('Random deals are a poor test for aligned loops: at 6 and 8 values, where aligned loops exist, they are rarely hit',
     './battles q 6 4 0 4 50000000 3 | sed -n 1,3p; ./battles q 8 4 0 4 50000000 3 | sed -n 1,3p; ./battles q 7 4 0 4 200000000 11 | sed -n 1,3p;'
     ' ./battles r 7 4 0 4 20000000 7 | sed -n 1,4p'),
    ('Every deal of 5 values in 4 suits (20 cards; 20!/4!^5 = 305,540,235,000 deals, 152,770,174,200 up to exchanging the players):'
     ' aligned loops (mode A) and every game played to its end (mode F), the merged result files',
     copy_then('data/v5_aligned.chunks', './battles A 5 4 0 4 6 FILE | grep -v resuming') + ' && ' +
     copy_then('data/v5_full.chunks', './battles F 5 4 0 4 6 FILE | grep -v resuming')),
    ("The battle-free route: Spivey's 52-card deal and the Theorem-3 cycles (uses ../counting/t3_count.py)",
     'python battle_free/spivey52_meetings.py; python battle_free/t3_meetings.py 20,4 28,4 36,4 40,8 44,4 52,4;'
     ' python battle_free/tie_free_assign.py 20,4 28,4 36,4 44,4 52,4'),
    ('Every orbit of the phase map we know has period 4', 'python checks/phase_orbits.py'),
    ("Every loop listed in Delahaye and Mathieu's records file, played by the second engine (checks/war_engine.py)", 'python checks/replay_records.py'),
    ('Stacking, every deal of the 8-card atom patterns, and the 12-card loops with a 5-copy value, second engine', 'python checks/stack_checks.py'),
    ("The same two checks with the cycle search done by Delahaye and Mathieu's bataille.py (recorded; not re-run here)", 'cat checks/dm_crosscheck.txt'),
    ('Second shape search (shape_orbits.py, written independently of shapes.cpp): 8 cards at periods 1, 2, 4 with and without'
     ' the 4-copy limit (last argument 4 or 0); 12 cards at periods 1, 2, 4, 8 with the limit and 4 without',
     'for a in "8 1 4" "8 1 0" "8 2 4" "8 2 0" "8 4 4" "8 4 0" "12 1 4" "12 2 4" "12 4 4" "12 4 0" "12 8 4"; do'
     ' echo "\\$ python shape_orbits.py $a"; python shape_orbits.py $a; done'),
]

out = ['Output of the searches in this directory, as the programs print it. Each block gives the command (bash, run from',
       'this directory), then its output. Written by make_results.py on ' + time.strftime('%Y-%m-%d') + '.', '']
out += ['== Sources: md5 of every program and script in this directory']
for root, dirs, files in sorted(os.walk(HERE)):
    dirs[:] = sorted(d for d in dirs if d not in ('data', '__pycache__'))
    for f in sorted(files):
        if f.endswith(('.cpp', '.py')):
            p = os.path.join(root, f)
            with open(p, 'rb') as fh:
                out.append(hashlib.md5(fh.read()).hexdigest() + '  ' + os.path.relpath(p, HERE).replace(os.sep, '/'))
out.append('')
NOWINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)    # no console window when this runs detached on Windows
for title, cmd in BLOCKS:
    t0 = time.time()
    r = subprocess.run([BASH, '-c', cmd.replace('./battles', './battles' + EXE).replace('./shapes', './shapes' + EXE)], cwd=HERE,
                       capture_output=True, text=True, env=dict(os.environ, PYTHONIOENCODING='utf-8'), creationflags=NOWINDOW)
    shown = cmd.replace(TMP + '/', '$TMP/')
    out += ['== ' + title, '$ ' + shown, (r.stdout + r.stderr).replace(TMP + '/', '$TMP/').rstrip('\n'), '']
    print('%-70s %.0fs' % (title[:70], time.time() - t0), flush=True)

# the Theorem-3 and atom checks: make_results_C.py writes RESULTS_C.txt; its blocks go here, after its own header
t0 = time.time()
r = subprocess.run([sys.executable, 'make_results_C.py'], cwd=HERE, capture_output=True, text=True,
                   creationflags=NOWINDOW)
rc = os.path.join(HERE, 'RESULTS_C.txt')
if r.returncode == 0 and os.path.exists(rc):
    with open(rc, encoding='ascii') as f:
        lines = f.read().rstrip('\n').split('\n')
    start = next(i for i, l in enumerate(lines) if l.startswith('== '))
    out += ['(The next blocks are written by make_results_C.py; its commands run from the folder named before them.)', '']
    out += lines[start:] + ['']
    os.remove(rc)
else:
    out += ['== make_results_C.py failed', (r.stdout + r.stderr).rstrip('\n'), '']
print('%-70s %.0fs' % ('make_results_C.py (Theorem-3 and atom checks)', time.time() - t0), flush=True)

with open(os.path.join(HERE, 'RESULTS.txt'), 'w', encoding='ascii', errors='replace', newline='') as f:
    f.write('\n'.join(out) + '\n')
shutil.rmtree(TMP, ignore_errors=True)
