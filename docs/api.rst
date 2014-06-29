.. _pyramid_zodbconn_api:

:mod:`pyramid_zodbconn` API
---------------------------

.. automodule:: pyramid_zodbconn

.. autofunction:: includeme

.. autofunction:: get_connection

Connection Events
-----------------

All connection events have two attributes: ``conn`` and ``request``.  ``conn``
is the ZODB connection related to the event, ``request`` is the request which
caused the event.

.. autoclass:: ZODBConnectionOpened

.. autoclass:: ZODBConnectionWillClose

.. autoclass:: ZODBConnectionClosed
