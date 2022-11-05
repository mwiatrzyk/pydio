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

0.1.0rc1 (2021-02-04)
---------------------

### Feat

- first released tag
