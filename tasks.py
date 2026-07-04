from invoke.tasks import task
from invoke.context import Context


@task(help={"fix": "Fix formatting if needed."})
def check_formatting(ctx: Context, fix: bool = False):
    """Check if the code is well formatted."""
    ctx.run(f"ruff format {'--check' if not fix else ''} .")


@task(help={"fix": "Try fixing linting issues."})
def check_lint(ctx: Context, fix: bool = False):
    """Run linting checks."""
    ctx.run(f"ruff check {'--fix' if fix else ''}")


@task
def check_typing(ctx: Context):
    """Run type hinting checks."""
    ctx.run("mypy pydio")


@task
def check_tests(ctx: Context):
    """Run unit tests."""
    ctx.run("pytest tests/")


@task(help={"fail_under": "The minimum accepted coverage level."})
def check_coverage(ctx: Context, fail_under: int=98):
    """Run tests with coverage check."""
    ctx.run(
        f"pytest tests/ --cov=pydio --cov-branch --cov-fail-under={fail_under} "
        "--cov-report=html:reports/coverage/html "
        "--cov-report=xml:reports/coverage/coverage.xml"
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
    ctx.run("inv check-coverage")
    ctx.run("inv check-docs")


@task(help={"port": "The bind port for local HTTP server."})
def serve_coverage(ctx: Context, port: int=8000):
    """Generate coverage report and use Python's built-in HTTP server to
    serve it locally."""
    ctx.run("inv check-coverage --fail-under=0")
    ctx.run(f"python -m http.server {port} -d reports/coverage/html")


@task
def build_docs(ctx: Context):
    """Build Sphinx documentation."""
    ctx.run("sphinx-build -M html docs/source docs/build")


@task
def build_pkg(ctx: Context):
    """Build a distribution package."""
    ctx.run("uv build")


@task(build_docs)
def serve_docs(ctx: Context, port: int=8000):
    """Build documentation and serve it locally using built-in HTTP server."""
    ctx.run(f"python -m http.server {port} -d docs/build/html")


@task
def clean(ctx: Context):
    """Clean working directory."""
    ctx.run('find . -name "*.pyc" -delete')
    ctx.run('find . -type d -name "__pycache__" -empty -delete')
