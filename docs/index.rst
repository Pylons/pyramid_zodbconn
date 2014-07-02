pyramid_zodbconn
================

Overview
--------

A package which provides integration between the Pyramid web application
server and the :term:`ZODB` object database.

It will run under CPython 2.5, 2.6, and 2.7.  It will not run under PyPy or
Jython.  It requires ZODB >= 3.10.0.

Installation
------------

Install using setuptools, e.g. (within a virtualenv)::

  $ easy_install pyramid_zodbconn

Setup
-----

Once ``pyramid_zodbconn`` is installed, you must use the ``config.include``
mechanism to include it into your Pyramid project's configuration.  In your
Pyramid project's ``__init__.py``:

.. code-block:: python
   :linenos:

   config = Configurator(.....)
   config.include('pyramid_zodbconn')

Alternately you can use the ``pyramid.includes`` configuration value in your
``.ini`` file:

.. code-block:: ini
   :linenos:

   [app:myapp]
   pyramid.includes = pyramid_zodbconn

Using
-----

For :mod:`pyramid_zodbconn` to work properly, you must add at least one
setting to your of your Pyramid's ``.ini`` file configuration (or to the
``settings`` dictionary if you're not using ini configuration):
``zodbconn.uri``.  For example:

.. code-block:: ini

   [app:myapp]
   ...
   zodbconn.uri = zeo://localhost:9991?cache_size=25MB
   ...

The ``zodbconn.uri`` parameter is a URL which describes a ZODB database.

Once you've both included the ``pyramid_zodbconn`` into your configuration
via ``config.include('pyramid_zodbconn')`` and you've added a
``zodbconn.uri`` setting to your configuration, you can then use the
:func:`pyramid_zodbconn.get_connection` API in your Pyramid application, most
commonly in a Pyramid *root factory*:

.. code-block:: python
   :linenos:

    from pyramid_zodbconn import get_connection
    from persistent.mapping import PersistentMapping

    class MyModel(PersistentMapping):
        __parent__ = __name__ = None

    def root_factory(request):
        conn = get_connection(request)
        zodb_root = conn.root()
        if not 'app_root' in zodb_root:
            app_root = MyModel()
            zodb_root['app_root'] = app_root
            import transaction
            transaction.commit()
        return zodb_root['app_root']

The :func:`pyramid_zodbconn.get_connection` API returns a ZODB connection to
the main database you've specified via ``zodbconn.uri`` in your
configuration.

When the request is finalized, the connection you've opened via
``get_connection`` will be closed.

Named Databases
---------------

If you need to use more than one ZODB database in your Pyramid application,
you can use *named* databases via configuration.  Named databases are
specified by ``zodbconn.uri.thename`` in settings configuration.  For
example:

.. code-block:: ini

   [app:myapp]
   ...
   zodbconn.uri = zeo://localhost:9991?cache_size=25MB
   zodbconn.uri.sessions = zeo://localhost:9992?cache_size=100MB
   ...

Once this is done, you can use :func:`pyramid_zodbconn.get_connection` to
obtain a reference to each of the named databases:

        main_conn = get_connection(request) # main database
        sessions_conn = get_connection(request, 'sessions')

The ``zodbconn.uri.sessions`` parameter example above is a URI which
describes a ZODB database, in the same format as ``zodbconn.uri``.  You can
combine named and unnamed database configuration in the same application.
You *must* have at least one primary database to use named databases.

.. note::

   Named database support is new as of ``pyramid_zodbconn`` 0.3.

URI Schemes
-----------

The URI schemes currently recognized in the ``zodbconn.uri`` setting are
``file://``, ``zeo://``, ``zconfig://`` and ``memory://``.  Documentation for
these URI scheme syntaxes are below.

``file://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~

The ``file://`` URI scheme can be passed as ``zodbconn.uri`` to create a ZODB
FileStorage database factory.  The path info section of this scheme should
point at a filesystem file path that should contain the filestorage data.
For example::

  file:///my/absolute/path/to/Data.fs

The URI scheme also accepts query string arguments.  The query string
arguments honored by this scheme are as follows.

FileStorage constructor related
+++++++++++++++++++++++++++++++

These arguments generally inform the FileStorage constructor about
values of the same names.

create
  boolean
read_only
  boolean
quota
  bytesize

Database-related
++++++++++++++++

These arguments relate to the database (as opposed to storage)
settings.

database_name
  string

Connection-related
++++++++++++++++++

These arguments relate to connections created from the database.

connection_cache_size
  integer (default 10000)
connection_pool_size
  integer (default 7)

Blob-related
++++++++++++

If these arguments exist, they control the blob settings for this
storage.

blobstorage_dir
  string
blobstorage_layout
  string

Misc
++++

demostorage 
  boolean (if true, wrap FileStorage in a DemoStorage)

Example
+++++++

An example that combines a path with a query string::

   file:///my/Data.fs?connection_cache_size=100&blobstorage_dir=/foo/bar

``zeo://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~

The ``zeo://`` URI scheme can be passed as ``zodbconn.uri`` to create a ZODB
ClientStorage database factory. Either the host and port parts of this scheme
should point at a hostname/portnumber combination e.g.::

  zeo://localhost:7899

Or the path part should point at a UNIX socket name::

  zeo:///path/to/zeo.sock

The URI scheme also accepts query string arguments.  The query string
arguments honored by this scheme are as follows.

ClientStorage-constructor related
+++++++++++++++++++++++++++++++++

These arguments generally inform the ClientStorage constructor about
values of the same names.

storage
  string
cache_size
  bytesize
name
  string
client
  string
debug
  boolean
var
  string
min_disconnect_poll
  integer
max_disconnect_poll
  integer
wait
  boolean
wait_timeout
  integer
read_only
  boolean
read_only_fallback
  boolean
username
  string
password
  string
realm
  string
blob_dir
  string
shared_blob_dir
  boolean

Misc
++++

demostorage
  boolean (if true, wrap ClientStorage in a DemoStorage)

Connection-related
++++++++++++++++++

These arguments relate to connections created from the database.

connection_cache_size
  integer (default 10000)
connection_pool_size
  integer (default 7)

Database-related
++++++++++++++++

These arguments relate to the database (as opposed to storage)
settings.

database_name
  string

Example
+++++++

An example that combines a path with a query string::

  zeo://localhost:9001?connection_cache_size=20000

``zconfig://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``zconfig://`` URI scheme can be passed as ``zodbconn.uri`` to create any
kind of storage that ZODB can load via ZConfig. The path info section of this
scheme should point at a ZConfig file on the filesystem. Use an optional
fragment identifier to specify which database to open. This URI scheme does
not use query string parameters.

Examples
++++++++

An example ZConfig file::

    <zodb>
      <mappingstorage>
      </mappingstorage>
    </zodb>

If that configuration file is located at /etc/myapp/zodb.conf, use the
following URI to open the database::

    zconfig:///etc/myapp/zodb.conf

A ZConfig file can specify more than one database.  For example::

    <zodb temp1>
      <mappingstorage>
      </mappingstorage>
    </zodb>
    <zodb temp2>
      <mappingstorage>
      </mappingstorage>
    </zodb>

In that case, use a URI with a fragment identifier::

    zconfig:///etc/myapp/zodb.conf#temp1

``memory://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``memory://`` URI scheme can be passed as ``zodbconn.uri`` to create a
ZODB MappingStorage (memory-based) database factory.  The path info section
of this scheme should be a storage name.  For example::

  memory://storagename

However, the storage name is usually omitted, and the most common form is::

  memory://

The URI scheme also accepts query string arguments.  The query string
arguments honored by this scheme are as follows.

Database-related
++++++++++++++++

These arguments relate to the database (as opposed to storage)
settings.

database_name
  string

Connection-related
++++++++++++++++++

These arguments relate to connections created from the database.

connection_cache_size
  integer (default 10000)
connection_pool_size
  integer (default 7)

Example
+++++++

An example that combines a dbname with a query string::

   memory://storagename?connection_cache_size=100&database_name=fleeb

Events
------

All events are sent via the standard Pyramid ``registry.notify`` interface and
can be subscribed to using the ``config.add_subscriber`` API in Pyramid.

When a connection is opened, the
:class:`pyramid_zodbconn.ZODBConnectionOpened` event is sent.

Just before a connection is closed, the
:class:`pyramid_zodbconn.ZODBConnectionWillClose` event is sent.

When a connection is closed, the
:class:`pyramid_zodbconn.ZODBConnectionClosed` event is sent.

Transfer Log
------------

Add the key ``zodbconn.transferlog`` to your deployment settings to have
``pyramid_zodbconn`` send information about the ZODB stoage loads and stores
caused by each request sent to the system.  The ``zodbconn.transferlog`` key
can either be a filename or it can be empty, which indicates that the transfer
log should be sent to stdout.

For example::

  zodbconn.transferlog = /some/file/transfer.log

The transfer log is written in CSV format.  Each line is in the format::

  timestamp, request_method, url, elapsed_secs, loads, stores

For example::

  "2014-07-02 13:44:18", "GET", "/manage/@@contents", 28.47, 23580, 0
  "2014-07-02 13:44:18", "GET", "/manage/auditstream-sse", 0.02, 0, 0
  "2014-07-02 13:44:18", "GET", "/sdistatic/css/sdi_bootstrap.css", 0.00, 0, 0
  "2014-07-02 13:44:18", "GET", "/sdistatic/js/jquery-2.0.3.js", 0.00, 0, 0
  "2014-07-02 13:44:18", "GET", "/sdistatic/js/bootstrap.js", 0.00, 0, 0
  "2014-07-02 13:44:18", "GET", "/sdistatic/js/sdi.js", 0.00, 0, 0

If you only want to write transfer log entries for requests that take over a
certain amount of time, you can use the ``zodbconn.transferlog_threshhold``
setting.  It should be an integer representing a number of seconds.  If the
request consumes more than this number of seconds, a transfer log line will be
written, otherwise no transfer log line will be written.

For example::

  zodbconn.transferlog_threshhold = 2

More Information
----------------

.. toctree::
   :maxdepth: 1

   api.rst
   glossary.rst


Reporting Bugs / Development Versions
-------------------------------------

Visit http://github.com/Pylons/pyramid_zodbconn to download development or
tagged versions.

Visit http://github.com/Pylons/pyramid_zodbconn/issues to report bugs.

Indices and tables
------------------

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
