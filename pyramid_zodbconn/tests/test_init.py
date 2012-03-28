import unittest
from pyramid import testing

class Test_get_connection(unittest.TestCase):
    def _callFUT(self, request, dbname=None):
        from pyramid_zodbconn import get_connection
        return get_connection(request, dbname=dbname)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.registry._zodb_databases = {None:DummyDB()}
        return request

    def test_without_include(self):
        from pyramid.exceptions import ConfigurationError
        request = self._makeRequest()
        del request.registry._zodb_databases
        self.assertRaises(ConfigurationError, self._callFUT, request)
    
    def test_without_zodb_database(self):
        from pyramid.exceptions import ConfigurationError
        request = self._makeRequest()
        del request.registry._zodb_databases[None]
        self.assertRaises(ConfigurationError, self._callFUT, request)

    def test_without_zodb_database_named(self):
        from pyramid.exceptions import ConfigurationError
        request = self._makeRequest()
        self.assertRaises(ConfigurationError, self._callFUT, request, 'wont')
        
    def test_zodb_conn_already_exists(self):
        request = self._makeRequest()
        dummy_conn = DummyConnection()
        request._zodb_conns = {}
        request._zodb_conns[None] = dummy_conn
        conn = self._callFUT(request)
        self.assertEqual(conn, dummy_conn)

    def test_zodb_conn_new(self):
        request = self._makeRequest()
        conn = self._callFUT(request)
        self.assertEqual(conn, 
                         request.registry._zodb_databases[None].connection)
        self.assertEqual(len(request.finished_callbacks), 1)
        callback = request.finished_callbacks[0]
        self.assertFalse(conn.closed)
        callback(request)
        self.assertTrue(conn.closed)
        self.assertTrue(conn.transaction_manager.aborted)

class Test_includeme(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _callFUT(self, config, db_from_uri=None):
        config.captured_uris = []
        self.db = DummyDB()
        if db_from_uri is None:
            def db_from_uri(uri):
                config.captured_uris.append(uri)
                return self.db
        from pyramid_zodbconn import includeme
        return includeme(config, db_from_uri=db_from_uri)

    def test_with_uri(self):
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self._callFUT(self.config)
        self.assertEqual(self.config.captured_uris, ['uri'])
        self.assertEqual(self.config.registry._zodb_databases[None], self.db)

    def test_without_uri(self):
        self._callFUT(self.config)
        self.assertEqual(self.config.registry._zodb_databases, {})

    def test_with_named_uris(self):
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self.config.registry.settings['zodbconn.uri.foo'] = 'uri.foo'
        self.config.registry.settings['zodbconn.uri.bar'] = 'uri.bar'
        self._callFUT(self.config)
        self.assertEqual(self.config.captured_uris, 
                         ['uri', 'uri.foo', 'uri.bar'])
        self.assertEqual(self.config.registry._zodb_databases[None], self.db)
        self.assertEqual(self.config.registry._zodb_databases['foo'], self.db)
        self.assertEqual(self.config.registry._zodb_databases['bar'], self.db)

class Test_db_from_uri(unittest.TestCase):
    def test_it(self):
        from pyramid_zodbconn import db_from_uri
        from ZODB.MappingStorage import MappingStorage
        storage = MappingStorage()
        def resolve_uri(uri):
            def storagefactory():
                return storage
            return storagefactory, {}
        db = db_from_uri('whatever', resolve_uri=resolve_uri)
        self.assertEqual(db._storage, storage)

class DummyDB:
    def __init__(self):
        self.databases = {'unnamed': self}
        self.connection = DummyConnection()
    def open(self):
        return self.connection

class DummyTransactionManager:
    aborted = False
    def abort(self):
        self.aborted = True

class DummyConnection:
    closed = False

    def __init__(self):
        self.transaction_manager = DummyTransactionManager()

    def close(self):
        self.closed = True

