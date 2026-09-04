import os
import pathlib
import shutil

from invoke.tasks import task
from invoke.context import Context

ROOT_DIR = pathlib.Path(__file__).parent.absolute()


@task(help={"fix": "Fix formatting if needed."})
def check_formatting(ctx: Context, fix: bool = False):
    """Check if the code is well formatted."""
    ctx.run(f"ruff format {'--check' if not fix else ''} .")


@task
def format(ctx: Context):
    """Format code using `ruff format` tool."""
    ctx.run("inv check-formatting --fix")


@task(help={"fix": "Try fixing linting issues."})
def check_lint(ctx: Context, fix: bool = False):
    """Run linting checks."""
    ctx.run(f"ruff check {'--fix' if fix else ''} --exclude api.py --exclude pydio/v1/_compat/__init__.py")


@task
def check_typing(ctx: Context):
    """Run type hinting checks."""
    ctx.run("mypy pydio")


@task
def check_tests(ctx: Context):
    """Run unit tests."""
    ctx.run("pytest tests/")


@task(help={"fail_under": "The minimum accepted coverage level."})
def check_coverage(ctx: Context, fail_under: int = 98):
    """Run tests with coverage check."""
    ctx.run(
        f"pytest tests/ --cov=pydio --cov-branch --cov-fail-under={fail_under} "
        "--cov-report=html:.reports/coverage/html "
        "--cov-report=xml:.reports/coverage/coverage.xml"
    )


@task
def check_docs(ctx: Context):
    """Run documentation tests."""
    ctx.run("sphinx-build -M doctest docs/source docs/build")


@task(help={"fix": "Try fixing issues."})
def check(ctx: Context, fix: bool = False):
    """Run all checks."""
    ctx.run(f"inv check-formatting {'--fix' if fix else ''}")
    ctx.run(f"inv check-lint {'--fix' if fix else ''}")
    ctx.run("inv check-typing")
    ctx.run("inv check-tests")
    ctx.run("inv check-coverage -f95")
    ctx.run("inv check-docs")


@task(help={"port": "The bind port for local HTTP server."})
def serve_coverage(ctx: Context, port: int = 8000):
    """Generate coverage report and use Python's built-in HTTP server to
    serve it locally."""
    ctx.run("inv check-coverage --fail-under=0")
    ctx.run(f"python -m http.server {port} -d .reports/coverage/html")


@task
def build_docs(ctx: Context):
    """Build Sphinx documentation."""
    ctx.run("sphinx-build -M html docs/source docs/build")


@task
def build_pkg(ctx: Context):
    """Build a distribution package."""
    ctx.run("uv build")


@task(build_docs)
def serve_docs(ctx: Context, port: int = 8000):
    """Build documentation and serve it locally using built-in HTTP server."""
    ctx.run(f"python -m http.server {port} -d docs/build/html")


@task
def clean(ctx: Context):
    """Clean working directory."""
    ctx.run('find . -name "*.pyc" -delete')
    ctx.run('find . -type d -name "__pycache__" -empty -delete')
    ctx.run("git clean -xdf --exclude .venv")


@task(help={"force": "Replace existing docs with newly generated ones."})
def gen_api_docs(ctx: Context, force: bool = False):
    """Rebuild API docs sources."""

    def write_module(relpath: pathlib.Path, file_without_ext: str):
        module_name = f"{relpath}.{file_without_ext}".replace(os.path.sep, ".")
        rows = [f"**{module_name}**"]
        rows.append("=" * len(rows[0]))
        rows.extend(
            [f".. automodule:: {module_name}", "    :members:", "    :no-index:" if file_without_ext == "api" else ""]
        )
        fullpath = target_dir / relpath / f"{file_without_ext}.rst"
        fullpath.parent.mkdir(parents=True, exist_ok=True)
        fullpath.write_text("\n".join(x for x in rows if x))

    def write_index(entries: list[str]):
        rows = ["API Reference"]
        rows.extend(["=" * len(rows[0]), ".. toctree::", "    :maxdepth: 1", ""])
        for entry in sorted(entries):
            rows.append(f"    {entry}")
        fullpath = target_dir / "index.rst"
        fullpath.write_text("\n".join(rows))

    cwd = pathlib.Path().cwd()
    if cwd != ROOT_DIR:
        raise RuntimeError(f"This command must be called from a PyDIO repository root directory: {ROOT_DIR}")
    source_dir = cwd / "pydio"
    target_dir = cwd / "docs" / "source" / "api"
    if target_dir.exists():
        if not force:
            raise RuntimeError(
                f"The target directory already exists: {target_dir}. Try running again with --force option enabled to override."
            )
        shutil.rmtree(target_dir)
    index_entries = []
    for path, dirs, files in os.walk(source_dir):
        relpath = pathlib.Path(path).relative_to(source_dir.parent)
        names = str(relpath).split(os.path.sep)
        is_public = all(not x.startswith("_") for x in names)
        if not is_public:
            continue
        for dir in filter(lambda x: not x.startswith("_"), dirs):
            index_entries.append(str(relpath / dir))
            write_module(relpath, dir)
        for file in filter(lambda x: not x.startswith("_") and x.endswith(".py"), files):
            file_without_ext = file[: file.rfind(".py")]
            index_entries.append(str(relpath / file_without_ext))
            write_module(relpath, file_without_ext)
    write_index(index_entries)
