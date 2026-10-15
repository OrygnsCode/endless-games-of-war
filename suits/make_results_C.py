# Writes RESULTS_C.txt: each check of the Theorem-3 and atom parts of the suits section, with its command and output.
# Run from suits/:  python make_results_C.py
import hashlib, os, subprocess, sys, time
from importlib.metadata import version

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["theorem3/t3_suits.py", "theorem3/t3_routes.py", "theorem3/spivey52.py", "theorem3/courbet44.py", "atoms.py"]
CHECKS = [
    ("Spivey's 52-card deal: cycle length, category sizes, and which categories meet",
     "theorem3", ["spivey52.py"]),
    ("Courbet's 44-card loop under Delahaye and Mathieu's rules: cycle, ties, runs, categories, shape",
     "theorem3", ["courbet44.py"]),
    ("Theorem-3 shapes with suits: level sizes, complete meeting, rankings with 2 and 4 suits",
     "theorem3", ["t3_suits.py", "28", "44", "52", "60", "76", "92", "68:1", "68:2", "68:4"]),
    ("Route prediction against a full cycle, every shape with n = m * 2^v <= 124, 1 <= v <= 3",
     "theorem3", ["t3_routes.py", "all", "124"]),
    ("Aligned loops and the 8-card atom (Delahaye and Mathieu's rules)",
     ".", ["atoms.py"]),
]

out = ["Output of the checks for the Theorem-3 and atom parts of the suits section, as the programs print it.",
       "Each block gives the directory and command (from suits/), then the output. Written by make_results_C.py on "
       f"{time.strftime('%Y-%m-%d %H:%M')}.", "",
       "== Sources and versions", "$ md5 of the scripts; python and python-sat versions"]
for f in SCRIPTS:
    out.append(hashlib.md5(open(os.path.join(HERE, f), "rb").read()).hexdigest() + "  " + f)
out.append(f"python {sys.version.split()[0]}, python-sat {version('python-sat')}")
for title, folder, cmd in CHECKS:
    r = subprocess.run([sys.executable, "-u"] + cmd, cwd=os.path.join(HERE, folder), capture_output=True, text=True,
                       timeout=3600)
    shown = ("cd theorem3; " if folder != "." else "") + "python " + " ".join(cmd)
    out += ["", "== " + title, "$ " + shown] + r.stdout.rstrip("\n").split("\n")
    if r.returncode or r.stderr.strip(): out += ["(exit code %d)" % r.returncode] + r.stderr.rstrip("\n").split("\n")
open(os.path.join(HERE, "RESULTS_C.txt"), "w", encoding="ascii", newline="\n").write("\n".join(out) + "\n")
print("wrote RESULTS_C.txt")
