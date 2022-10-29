# ---------------------------------------------------------------------------
# tasks.py
#
# Copyright (C) 2021 - 2022 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------

import os

import invoke

import pydio


@invoke.task
def qa_test_unit(ctx):
    """Run unit tests."""
    ctx.run('pytest tests/')


@invoke.task
def qa_test_docs(ctx):
    """Run documentation tests."""
    ctx.run('sphinx-build -M doctest docs/source docs/build')


@invoke.task(qa_test_unit, qa_test_docs)
def qa_test(_):
    """Run all tests."""


@invoke.task
def qa_cov(ctx, fail_under=94):
    """Run code coverage check."""
    ctx.run(
        'pytest tests/ --cov=pydio --cov-fail-under={fail_under} '
        '--cov-report=html:reports/coverage/html '
        '--cov-report=xml:reports/coverage/coverage.xml'.format(
            fail_under=fail_under
        )
    )


@invoke.task
def serve_cov(ctx, host='localhost', port=8000):
    """Generate coverage report and use Python's built-in HTTP server to
    serve it locally."""
    ctx.run('inv coverage -f0')
    ctx.run(
        'python -m http.server {} -d reports/coverage/html -b {}'.format(
            port, host
        )
    )


@invoke.task
def qa_lint_code(ctx):
    """Run linter on source files."""
    args = ['pylint -f colorized --fail-under=9.0 pydio']
    args.extend([
        '-d missing-module-docstring',
        '-d missing-class-docstring',
        '-d missing-function-docstring',
    ])
    ctx.run(' '.join(args))


@invoke.task
def qa_lint_tests(ctx):
    """Run linter on test files."""
    args = ['pylint tests -f colorized --fail-under=9.0']
    args.extend([
        '-d missing-module-docstring',
        '-d missing-class-docstring',
        '-d missing-function-docstring',
        '-d attribute-defined-outside-init',
        '-d too-few-public-methods',
        '-d too-many-public-methods',
        '-d no-self-use',
        '-d line-too-long',
    ])
    ctx.run(' '.join(args))


@invoke.task(qa_lint_code, qa_lint_tests)
def qa_lint(_):
    """Run all linters."""


@invoke.task(qa_test, qa_cov, qa_lint)
def qa(_):
    """Run all code quality checks."""


@invoke.task
def tox(ctx, parallel=False, env=None):
    """Run all code quality checks using tox.

    This will by default run checks on all supported Python versions.

    -p, --parallel
        If set, all environments will be tested simultaneously, with a level
        of concurrency up to available CPU cores

    -e, --env
        Run tox with specified environment only, f.e. py36
    """
    args = ['tox']
    if parallel:
        args.append('-p=auto')
    if env:
        args.append('-e {}'.format(env))
    ctx.run(' '.join(args))


@invoke.task
def adjust_formatting(ctx):
    """Run code formatting tools."""
    ctx.run(
        'autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables --expand-star-imports pydio tests scripts tasks.py'
    )
    ctx.run('isort --atomic pydio tests scripts tasks.py')
    ctx.run('yapf -i --recursive --parallel pydio tests scripts tasks.py')


@invoke.task
def adjust_copyright(ctx):
    """Update LICENSE file and license preambles in source files."""
    ctx.run(
        'scripts/licenser/licenser.py . --released={released} --author="{author}" -i "*.py" -i "*.rst" -e "*README.rst" -e "*CHANGELOG.rst" -e "*.git"'
        .format(released=pydio.__released__, author=pydio.__author__)
    )


@invoke.task(adjust_formatting, adjust_copyright)
def adjust(_):
    """Run all code fixers."""


@invoke.task
def build_docs(ctx):
    """Build Sphinx documentation."""
    ctx.run('sphinx-build -M html docs/source docs/build')


@invoke.task
def build_pkg(ctx):
    """Build distribution package."""
    ctx.run('poetry build')


@invoke.task(build_docs, build_pkg)
def build(_):
    """Build all."""


@invoke.task(build_docs)
def serve_docs(ctx, host='localhost', port=8000):
    """Generate documentation and use Python's built-in HTTP server to serve
    it locally."""
    ctx.run(
        'python -m http.server {} -d docs/build/html -b {}'.format(port, host)
    )


@invoke.task(
    help={
        'rc': 'Create a release candidate instead of regular version',
        'dev': 'Create a development release instead of regular version'
    }
)
def bump(ctx, rc=False, dev=False):
    """Bump version and create bump commit.

    This command bumps version according to arguments provided. For --rc, it
    will create next release candidate. For --dev, it will create development
    version tagged with current date and time. If no args are given, then next
    release is determined based on commit messages. Additionally, this command
    updates CHANGELOG.md.
    """

    def get_most_recent_tag():
        return ctx.run('git tag --sort=-committerdate | head -1').stdout.strip()

    def get_devrelease_number():
        return ctx.run(f'git rev-list --count {get_most_recent_tag()}..HEAD'
                       ).stdout.strip()

    if rc and dev:
        raise ValueError("cannot use both --rc and --dev options")
    args = ['cz', 'bump']
    if rc:
        args.append('--prerelease=rc')
    if dev:
        args.append(f"--devrelease={get_devrelease_number()}")
    ctx.run(' '.join(args))


@invoke.task(build_pkg)
def deploy_test(ctx):
    """Build and deploy library to test PyPI."""
    ctx.run(
        'twine upload --verbose --repository-url https://test.pypi.org/legacy/ dist/*',
        env={
            'TWINE_USERNAME': '__token__',
            'TWINE_PASSWORD': os.environ.get('TEST_PYPI_TOKEN')
        }
    )


@invoke.task(build_pkg)
def deploy_prod(ctx):
    """Deploy library to production PyPI."""
    ctx.run('twine upload --verbose dist/*')


@invoke.task
def clean(ctx):
    """Clean working directory."""
    ctx.run('find . -name "*.pyc" -delete')
    ctx.run('find . -type d -name "__pycache__" -empty -delete')
    ctx.run('rm -rf pydio/_version.py')
    ctx.run('rm -rf docs/build')
    ctx.run('rm -rf build dist')
    ctx.run('rm -rf *.egg-info')
    ctx.run('rm -rf .eggs')
    ctx.run('rm -rf reports')
