# ---------------------------------------------------------------------------
# tasks.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------

import json
import os
import re
import subprocess
import tempfile

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
        'dev': 'Create a development release instead of regular version',
        'dry_run': 'Do not commit anything. Instead, exit with 0 if bump would succeed or with 1 otherwise',
        'manual_version': 'Bump to provided manual version'
    }
)
def bump(ctx, rc=False, dev=False, dry_run=False, manual_version=None):
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
        tag = get_most_recent_tag()
        m = re.search(r'dev(\d+)$', tag)
        if m is None:
            return 1
        return int(m.group(1)) + 1

    ctx.run('inv adjust')
    if rc and dev:
        raise ValueError("cannot use both --rc and --dev options")
    args = ['cz', 'bump']
    if rc:
        args.append('--prerelease=rc')
    if dev:
        args.append(f"--devrelease={get_devrelease_number()}")
    if dry_run:
        args.append('--dry-run')
    if manual_version:
        args.append(manual_version)
    ctx.run(' '.join(args))
    ctx.run('inv qa')


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
    ctx.run(
        'twine upload --verbose dist/*',
        env={
            'TWINE_USERNAME': '__token__',
            'TWINE_PASSWORD': os.environ.get('PYPI_TOKEN')
        }
    )


@invoke.task(build_pkg)
def deploy_gh(ctx, tag, draft=False):
    """Deploy library to GitHub."""

    def run_subprocess(args: list) -> subprocess.CompletedProcess:
        return subprocess.run(args, capture_output=True, encoding='utf-8')

    def run_gh(args: list) -> dict:
        p = run_subprocess([
            'curl', '-X', 'POST', '-H', 'Accept: application/vnd.github+json',
            '-H', f"Authorization: Bearer {os.environ['GH_TOKEN']}"
        ] + args)
        return json.loads(p.stdout)

    def load_changelog():
        p = run_subprocess(['cz', 'changelog', '--dry-run', tag])
        return p.stdout

    def create_release(tag_name, body, draft=False):

        def write_params_json(filename):
            with open(filename, 'w') as fd:
                data = {
                    'tag_name': tag_name,
                    'name': tag_name,
                    'body': body,
                    'draft': draft
                }
                json.dump(data, fd)

        with tempfile.TemporaryDirectory() as tmpd:
            params_json = os.path.join(tmpd, 'params.json')
            write_params_json(params_json)
            return run_gh([
                'https://api.github.com/repos/mwiatrzyk/pydio/releases', '-d',
                f'@{params_json}'
            ])

    def upload_assets(dist_dir, release_id):
        for name in os.listdir(dist_dir):
            fullname = os.path.join(dist_dir, name)
            run_gh([
                '-H', 'Content-Type: application/octet-stream', '--data-binary',
                f'@{fullname}',
                f'https://uploads.github.com/repos/mwiatrzyk/pydio/releases/{release_id}/assets?name={name}'
            ])

    changelog = load_changelog()
    release_info = create_release(tag, changelog, draft=draft)
    if 'id' not in release_info:
        raise RuntimeError(release_info)
    upload_assets('dist', release_info['id'])


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
