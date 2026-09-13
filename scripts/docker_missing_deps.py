"""Which third-party modules does the runtime code import, and which are missing from this image?

Run inside the container. A clean environment is the only reliable way to see this: on a host with a fat venv every
import works and the manifest's gaps stay invisible until a deploy.
"""
import ast
import importlib.util
import pathlib
import sys

STDLIB = set(sys.stdlib_module_names)
ROOTS = ("server", "agents", "scripts", "tests")
SKIP_DIRS = {".venv", "node_modules", "__pycache__", "output", "data", ".git"}

MODULE_TO_PACKAGE = {
    "PIL": "pillow",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "google": "google-genai / google-adk",
    "mcp": "mcp",
    "litellm": "litellm",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "jinja2": "jinja2",
    "httpx": "httpx",
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "playwright": "playwright",
    "weasyprint": "weasyprint",
    "cachetools": "cachetools",
    "pydantic": "pydantic",
    "anyio": "anyio",
    "pytest": "pytest",
}


def local_module_names() -> set[str]:
    """Names that resolve to repo code rather than a package.

    A module imported by bare name can still be a sibling file: the engine's `s06_wacc`, the scripts' `utils` and
    `writer`. Those resolve at runtime because their directory joins sys.path, so counting them as missing packages
    buries the real answer under false alarms.
    """
    names: set[str] = set(ROOTS)
    for path in pathlib.Path(".").rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        names.add(path.stem)
        for parent in path.parents:
            if parent == pathlib.Path("."):
                break
            if parent.name:
                names.add(parent.name)
    for dirpath in pathlib.Path(".").rglob("__init__.py"):
        if any(part in SKIP_DIRS for part in dirpath.parts):
            continue
        names.add(dirpath.parent.name)
    return names


def main() -> int:
    local = local_module_names()
    imported: dict[str, set[str]] = {}
    for root in ROOTS:
        for path in pathlib.Path(root).rglob("*.py"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        imported.setdefault(top, set()).add(str(path))
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    top = node.module.split(".")[0]
                    imported.setdefault(top, set()).add(str(path))

    missing: dict[str, set[str]] = {}
    present: set[str] = set()
    for name, files in sorted(imported.items()):
        if name in STDLIB or name in local:
            continue
        if importlib.util.find_spec(name) is not None:
            present.add(name)
        else:
            missing[name] = files

    print(f"third-party imports found: {len(present) + len(missing)}")
    print(f"  importable here: {len(present)}")
    print(f"  MISSING: {len(missing)}")
    for name, files in missing.items():
        pkg = MODULE_TO_PACKAGE.get(name, name)
        where = sorted(files)[:2]
        print(f"    {name:<16} -> pip install {pkg:<18} used by {', '.join(where)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
