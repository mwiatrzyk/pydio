## v0.4.1 (2023-05-12)

### Fix

- properly close injector when exception thrown in teardown phase

## v0.4.0 (2023-05-06)

### Feat

- add support for Python 3.11
- extend API of IFactory.close for the purpose of solving issue #7

### Fix

- resolve issue #7

## v0.3.3 (2022-11-05)

### Fix

- deploy task no longer requires test jobs

## v0.3.2 (2022-11-05)

### Fix

- fix config.yml so that the job is triggered once tag is pushed

## v0.3.1 (2022-11-05)

### Fix

- make Changelog chapter in Sphinx documentation work again

## v0.3.0 (2022-11-05)

### Feat

- remove compatibility layer for no longer supported Python 3.6

## v0.2.1 (2022-11-05)

### Fix

- fix various CI issues (#6)

## v0.2.0 (2022-10-30)

### Feat

- project was moved from GitLab to GitHub (original repo can be found at
  https://gitlab.com/zef1r/pydio)
- testing and releasing is now done via CircleCI
- use **commitizen** tool (https://github.com/commitizen-tools/commitizen) to handle automatic version bump (based on Git log messages) and changelog management
- switch to **Poetry** (https://python-poetry.org/) from **Pipenv** (https://pipenv.pypa.io/en/latest/)
- successfully pass testing on Python 3.10
- drop support for Python 3.6 (as some development tools need >=3.7)
- use Markdown for README and CHANGELOG

## v0.1.0 (2021-02-15)

### Feat

- add quickstart tutorial to documentation
- add **env** parameter to `Injector.scoped()` method
- make code thread-safe
- part of the `Injector` class was made abstract in `pydio.base.IInjector` interface

### Fix

- fix annotations in `pydio.base` module

## v0.1.0rc4 (2021-02-10)

### Feat

- add missing support for async context manager in `pydio.injector.Injector` class
- add initial documentation draft with API docs
- add badges to the project
- change module name: `pydio.variant` -> `pydio.keys`
- redesign `pydio.base` module

### Fix

- added basic example to **README.rst**

## v0.1.0rc3 (2021-02-04)

### Fix

- fix in scripts and pipeline
- update **README.rst**

## v0.1.0rc2 (2021-02-04)

### Feat

- add `CHANGELOG.rst` file

### Fix
- add missing ``__version__`` attribute to ``pydio.__init__.py``
- fix pipeline issue about missing version info

## 0.1.0rc1 (2021-02-04)

### Feat

- first released tag
