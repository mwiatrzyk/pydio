## 0.5.0-dev (2026-09-04)

### Fix

- when `OutOfScopeError` is raised from a child provider, collect it and raise summarized error
- make tests pass on Python 3.13

### Feat

- add support for Python 3.12 and 3.13
- add a new v1 `provides` decorator
- create a v1 `Injector` implementation with tests
- add v1 `AsyncInjector` implementation with tests
- add async recursive lock implementation for a default asyncio backend
- add `inject_annotated` and `async_inject_annotated` helpers
- normalize exception handling
- add support for Python 3.14

## 0.4.1 (2023-05-12)

### Fix

- properly close injector when exception thrown in teardown phase

## 0.4.0 (2023-05-06)

### Fix

- resolve issue #7

### Feat

- extend API of IFactory.close for the purpose of solving issue #7
- add support for Python 3.11

## 0.3.3 (2022-11-05)

### Fix

- deploy task no longer requires test jobs

## 0.3.2 (2022-11-05)

### Fix

- fix config.yml so that the job is triggered once tag is pushed

## 0.3.1 (2022-11-05)

### Fix

- make Changelog chapter in Sphinx documentation work again

## 0.3.0 (2022-11-05)

### Feat

- remove compatibility layer for no longer supported Python 3.6

## 0.2.1 (2022-11-05)

### Fix

- fix various CI issues (#6)

## 0.2.0 (2022-10-30)

## 0.1.0 (2021-02-15)

## 0.1.0 (2021-02-10)

## 0.1.0 (2021-02-04)

## 0.1.0 (2021-02-04)

## 0.1.0 (2021-02-04)

Initial release.

