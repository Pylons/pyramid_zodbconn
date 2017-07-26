0.8.1 (2017-07-26)
------------------

- Avoid aborting at the end of a request if there is no active transaction.
  See https://github.com/Pylons/pyramid_zodbconn/pull/10

0.8 (2017-07-25)
----------------

- Open primary database using ``request.tm``, if present, as the transaction
  manager.  If not present, fall back to the default / global transaction
  manager.  Compatibility with ``pyramid_tm >= 0.11``, which allowed the
  user to specify an explicit per-request transaction factory.
  https://github.com/Pylons/pyramid_zodbconn/issues/6.

- Add support for Python 3.5 and 3.6.

- Drop support for Python 2.6, 3.2, and 3.3.

0.7 (2014-07-02)
----------------

- Change transfer log file format to include timestamp and elapsed time.

- Add ``zodbconn.transferlog_threshhold`` feature:  only log transfers if
  a request took > threshhold secs.

- Add ``docs`` section to tox.ini.

0.6 (2014-06-29)
----------------

- Add ``zodbconn.transferlog`` feature, which sends information about ZODB
  storage loads and stores to a CSV file.

- Add ZODBConnectionOpened, ZODBConnectionWillClose, and ZODBConnectionClosed
  events, which can be subscribed to.

0.5 (2014-01-04)
----------------

- Remove transitive dependencies of ``zodburi``.

- Add support for Python 3.2 / 3.3, and test them under ``tox``.

0.4 (2012-11-10)
----------------

- Configure database with ``ZODB.ActivityMonitor.ActivityMonitor``.

0.3 (2012-03-28)
----------------

- ``includeme`` docstring fix.

- Add named database capability (see new docs section entitled "Named
  Database Support").

0.2 (2011-08-24)
----------------

- Depend on the ``zodburi`` package rather than implementing our own URI
  resolvers and datatypes.

0.1 (2011-08-14)
----------------

- Initial release.
