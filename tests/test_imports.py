"""Every retained module imports, and nothing references a removed one."""

import ast
import importlib
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent

CORE_MODULES = [
    "src.common.features",
    "src.common.logger",
    "src.common.seed",
    "src.models.pregame.predictor",
    "src.models.pregame.train_ensemble_v2",
]


@pytest.mark.parametrize("module", CORE_MODULES)
def test_core_module_imports(module):
    assert importlib.import_module(module) is not None


def _tracked_python_files():
    out = subprocess.run(
        ["git", "ls-files", "src", "scripts", "tests"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    return [ROOT / f for f in out if f.endswith(".py")]


def test_no_file_imports_a_module_that_no_longer_exists():
    """Resolve every `src.*` import against the filesystem."""
    def exists(module: str) -> bool:
        base = ROOT / module.replace(".", "/")
        return base.with_suffix(".py").exists() or (base / "__init__.py").exists()

    broken = []
    for path in _tracked_python_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue

            for name in names:
                if name.split(".")[0] == "src" and not exists(name):
                    broken.append(f"{path.relative_to(ROOT)} -> {name}")

    assert not broken, "imports of modules that do not exist: " + "; ".join(broken)


def test_every_tracked_python_file_parses():
    for path in _tracked_python_files():
        ast.parse(path.read_text(), filename=str(path))
