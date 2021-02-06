# ---------------------------------------------------------------------------
# tasks.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------

import invoke

import pydio


@invoke.task
def test_unit(ctx):
    """Run unit tests."""
    ctx.run('pytest tests/')


@invoke.task
def test_docs(ctx):
    """Run documentation tests."""
    ctx.run('sphinx-build -M doctest docs/source docs/build')


@invoke.task(test_unit, test_docs)
def test(_):
    """Run all tests."""


@invoke.task
def coverage(ctx, fail_under=94):
    """Run code coverage check."""
    ctx.run(
        'pytest tests/ --cov=pydio --cov-fail-under={fail_under} '
        '--cov-report=html:reports/coverage/html '
        '--cov-report=xml:reports/coverage/coverage.xml'.format(
            fail_under=fail_under
        )
    )


@invoke.task
def serve_coverage(ctx, host='localhost', port=8000):
    """Generate coverage report and use Python's built-in HTTP server to
    serve it locally."""
    ctx.run('inv coverage -f0')
    ctx.run(
        'python -m http.server {} -d reports/coverage/html -b {}'.format(
            port, host
        )
    )


@invoke.task
def lint_code(ctx):
    """Run linter on source files."""
    args = ['pylint -f colorized --fail-under=9.0 pydio']
    args.extend(
        [
            '-d missing-module-docstring',
            '-d missing-class-docstring',
            '-d missing-function-docstring',
        ]
    )
    ctx.run(' '.join(args))


@invoke.task
def lint_tests(ctx):
    """Run linter on test files."""
    args = ['pylint tests -f colorized --fail-under=9.0']
    args.extend(
        [
            '-d missing-module-docstring',
            '-d missing-class-docstring',
            '-d missing-function-docstring',
            '-d attribute-defined-outside-init',
            '-d too-few-public-methods',
            '-d too-many-public-methods',
            '-d no-self-use',
            '-d line-too-long',
        ]
    )
    ctx.run(' '.join(args))


@invoke.task(lint_code, lint_tests)
def lint(_):
    """Run all linters."""


@invoke.task(test, coverage, lint)
def check(_):
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
        args.append('-p')
    if env:
        args.append('-e {}'.format(env))
    ctx.run(' '.join(args))


@invoke.task
def fix_formatting(ctx):
    """Run code formatting tools."""
    ctx.run(
        'autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables --expand-star-imports pydio tests scripts tasks.py'
    )
    ctx.run('isort --atomic pydio tests scripts tasks.py')
    ctx.run('yapf -i --recursive --parallel pydio tests scripts tasks.py')


@invoke.task
def fix_license(ctx):
    """Update LICENSE file and license preambles in source files."""
    ctx.run(
        'scripts/licenser/licenser.py . --released={released} --author="{author}" -i "*.py" -i "*.rst" -e "*README.rst" -e "*CHANGELOG.rst" -e "*.git"'
        .format(released=pydio.__released__, author=pydio.__author__)
    )


@invoke.task(fix_formatting, fix_license)
def fix(_):
    """Run all code fixers."""


@invoke.task
def build_docs(ctx):
    """Build Sphinx documentation."""
    ctx.run('sphinx-build -M html docs/source docs/build')


@invoke.task
def build_pkg(ctx):
    """Build distribution package."""
    ctx.run('python setup.py sdist bdist_wheel')


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


@invoke.task
def validate_tag(ctx, tag):
    """Check CHANGELOG.md and pydio/__init__.py agains given tag."""
    ctx.run('scripts/tag.py -c {}'.format(tag))


@invoke.task(fix)
def release(ctx, tag_or_version):
    """Run code fixers and update version in library code.

    This task should be run just before committing the last changes before
    next release. `tag_or_version` should contain version library will
    receive in PyPI. This can later be verified in CI with `validate-tag`
    task.
    """
    ctx.run('scripts/tag.py {}'.format(tag_or_version))


@invoke.task(build_pkg)
def deploy_test(ctx):
    """Build and deploy library to test PyPI."""
    ctx.run(
        'twine upload --verbose --repository-url https://test.pypi.org/legacy/ dist/*'
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
