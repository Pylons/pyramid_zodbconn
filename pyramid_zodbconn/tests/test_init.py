import unittest
from pyramid import testing

class Test_get_connection(unittest.TestCase):
    def _callFUT(self, request, dbname=None):
        from pyramid_zodbconn import get_connection
        return get_connection(request, dbname=dbname)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.registry._zodb_databases = {'':DummyDB()}
        return request

    def test_without_include(self):
        from pyramid.exceptions import ConfigurationError
        request = self._makeRequest()
        del request.registry._zodb_databases
        self.assertRaises(ConfigurationError, self._callFUT, request)
    
    def test_without_zodb_database(self):
        from pyramid.exceptions import ConfigurationError
        request = self._makeRequest()
        del request.registry._zodb_databases['']
        self.assertRaises(ConfigurationError, self._callFUT, request)

    def test_without_zodb_database_named(self):
        from pyramid.exceptions import ConfigurationError
        request = self._makeRequest()
        self.assertRaises(ConfigurationError, self._callFUT, request, 'wont')
        
    def test_primary_conn_already_exists(self):
        request = self._makeRequest()
        dummy_conn = DummyConnection()
        request._primary_zodb_conn = dummy_conn
        conn = self._callFUT(request)
        self.assertEqual(conn, dummy_conn)

    def test_secondary_conn(self):
        request = self._makeRequest()
        secondary = DummyConnection()
        dummy_conn = DummyConnection({'secondary':secondary})
        request._primary_zodb_conn = dummy_conn
        conn = self._callFUT(request, 'secondary')
        self.assertEqual(conn, secondary)
        
    def test_primary_conn_new(self):
        request = self._makeRequest()
        conn = self._callFUT(request)
        self.assertEqual(conn, 
                         request.registry._zodb_databases[''].connection)
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
            def db_from_uri(uri, dbname, dbmap):
                config.captured_uris.append(uri)
                dbmap[dbname] = self.db
                return self.db
        from pyramid_zodbconn import includeme
        return includeme(config, db_from_uri=db_from_uri)

    def test_with_uri(self):
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self._callFUT(self.config)
        self.assertEqual(self.config.captured_uris, ['uri'])
        self.assertEqual(self.config.registry._zodb_databases[''], self.db)

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
        self.assertEqual(self.config.registry._zodb_databases[''], self.db)
        self.assertEqual(self.config.registry._zodb_databases['foo'], self.db)
        self.assertEqual(self.config.registry._zodb_databases['bar'], self.db)

    def test_with_bad_named_uri(self):
        from pyramid.exceptions import ConfigurationError
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self.config.registry.settings['zodbconn.uri.'] = 'uri.foo'
        self.assertRaises(ConfigurationError, self._callFUT, self.config)

    def test_with_only_named_uri(self):
        from pyramid.exceptions import ConfigurationError
        self.config.registry.settings['zodbconn.uri.foo'] = 'uri.foo'
        self.assertRaises(ConfigurationError, self._callFUT, self.config)
        
class Test_db_from_uri(unittest.TestCase):
    def test_it(self):
        from pyramid_zodbconn import db_from_uri
        from ZODB.MappingStorage import MappingStorage
        storage = MappingStorage()
        def resolve_uri(uri):
            def storagefactory():
                return storage
            return storagefactory, {}
        db = db_from_uri('whatever', 'name', {}, resolve_uri=resolve_uri)
        self.assertEqual(db._storage, storage)

class DummyDB:
    def __init__(self, connections=None):
        self.databases = {'unnamed': self}
        self.connection = DummyConnection(connections)
    def open(self):
        return self.connection

class DummyTransactionManager:
    aborted = False
    def abort(self):
        self.aborted = True

class DummyConnection:
    closed = False

    def __init__(self, connections=None):
        self.transaction_manager = DummyTransactionManager()
        self.connections = connections or {}

    def close(self):
        self.closed = True

    def get_connection(self, name):
        return self.connections[name]
    

