"""Run unchanged pure tests and the real Core harness without the HA plugin."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
from importlib.metadata import version

ROOT = Path(__file__).resolve().parents[1]


def main():
    core = version("homeassistant")
    if core not in {"2026.11.0b0", "2026.11.0b1"}:
        raise SystemExit(f"Expected b0 or b1, got {core}")
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    pure = out / "pure-tests"
    pure.mkdir()
    for name in ("test_parser.py", "test_template_sources.py", "test_beta_sources.py"):
        shutil.copyfile(ROOT / "tests" / name, pure / name)
    env = dict(os.environ, PYTHONPATH=str(ROOT), BETA_EVIDENCE=str(out),
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "pytest_asyncio.plugin",
               "-p", "no:cacheprovider", "--asyncio-mode=auto", "-o",
               "asyncio_default_fixture_loop_scope=function", "--basetemp", str(out / "tmp"),
               "--junitxml", str(out / "results.xml"), str(ROOT / "beta_tests/test_runtime.py"), str(pure)]
    (out / "environment.txt").write_text(f"Python: {sys.version}\nHome Assistant: {core}\nCommand: {command!r}\n")
    with (out / "final.log").open("w") as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    print((out / "environment.txt").read_text())
    print((out / "final.log").read_text())
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
