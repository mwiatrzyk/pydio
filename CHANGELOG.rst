0.1.0 (2021-02-15)
------------------

**Added**

  * Add quickstart tutorial to documentation
  * Add **env** parameter to :meth:`pydio.injector.Injector.scoped` method
  * Add locks to make :class:`pydio.injector.Injector` and
    :class:`pydio.provider.Provider` thread-safe

**Changed**

  * Part of :class:`pydio.injector.Injector` interface made abstract in
    :class:`pydio.base.IInjector`

**Other**

  * Small cleanup in :mod:`pydio.base` module regarding annotations

0.1.0rc4 (2021-02-10)
---------------------

**Added**

  * Add missing support for async context manager in
    :class:`pydio.injector.Injector` class
  * Add initial documentation draft with API docs
  * Add some badges to the project

**Changed**

  * Improved README.rst file with simple example
  * Redesigned :mod:`pydio.base` module
  * Module renamed: pydio.variant -> :mod:`pydio.keys`

0.1.0rc3 (2021-02-04)
---------------------

* Fix in scripts and pipeline
* Update README.rst

0.1.0rc2 (2021-02-04)
---------------------

* Add ``CHANGELOG.rst`` file
* Add missing ``__version__`` attribute to ``pydio.__init__.py``
* Fix pipeline issue about missing version info
* Some other minor release fixes

0.1.0rc1 (2021-02-04)
---------------------

* First released tag
