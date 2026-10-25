import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MICROPYTHON_DIR = ROOT / "firmware/MaixPy/components/micropython/core"

if len(sys.argv) < 2:
    raise SystemExit("Usage: mpy_cross.py <source.py> [<source.py> ...]")

sources = []
for source in sys.argv[1:]:
    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    sources.append(source_path.resolve().relative_to(ROOT))

with tempfile.TemporaryDirectory() as temp_dir:
    build_dir = Path(temp_dir) / "micropython"
    shutil.copytree(MICROPYTHON_DIR, build_dir)

    if sys.platform == "darwin":
        persistent_code = build_dir / "py/persistentcode.c"
        persistent_code.write_text(
            persistent_code.read_text().replace(
                "defined(__i386__) || defined(__x86_64__) || defined(__unix__)",
                "defined(__i386__) || defined(__x86_64__) || defined(__unix__) || "
                "defined(__APPLE__)",
            )
        )
        gc_source = build_dir / "py/gc.c"
        gc_source.write_text(gc_source.read_text().replace("memset_s", "mp_memset_s"))

    cross_compiler_dir = build_dir / "mpy-cross"
    subprocess.run(["make", "-C", cross_compiler_dir], check=True)
    compiler = cross_compiler_dir / "mpy-cross"
    for source in sources:
        subprocess.run([compiler, source], cwd=ROOT, check=True)
