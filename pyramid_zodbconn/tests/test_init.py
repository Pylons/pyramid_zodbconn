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
    
    def _callFUT(self, config, db_from_uri=None, open=open):
        config.captured_uris = []
        self.db = DummyDB()
        if db_from_uri is None:
            def db_from_uri(uri, dbname, dbmap):
                config.captured_uris.append(uri)
                dbmap[dbname] = self.db
                return self.db
        from pyramid_zodbconn import includeme
        return includeme(config, db_from_uri=db_from_uri, open=open)

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
        self.assertEqual(sorted(self.config.captured_uris),
                         ['uri', 'uri.bar', 'uri.foo'])
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

    def test_activity_monitor_present(self):
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self._callFUT(self.config)
        db = self.config.registry._zodb_databases['']
        am = db.getActivityMonitor()
        self.assertTrue(am)

    def test_with_txlog_stdout(self):
        import sys
        L = []
        self.config.add_subscriber = lambda func, event: L.append((func, event))
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self.config.registry.settings['zodbconn.transferlog'] = ''
        self._callFUT(self.config)
        self.assertEqual(len(L), 2)
        self.assertEqual(L[0][0].__name__, 'start')
        self.assertEqual(L[1][0].__name__, 'end')
        self.assertEqual(self.config.registry._transferlog.stream, sys.stdout)

    def test_with_txlog_filename(self):
        L = []
        self.config.add_subscriber = lambda func, event: L.append((func, event))
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self.config.registry.settings['zodbconn.transferlog'] = 'foo'
        opened = []
        def fake_open(name, mode):
            opened.append((name, mode))
        self._callFUT(self.config, open=fake_open)
        self.assertEqual(len(L), 2)
        self.assertEqual(L[0][0].__name__, 'start')
        self.assertEqual(L[1][0].__name__, 'end')
        self.assertEqual(self.config.registry._transferlog.stream, None)
        self.assertEqual(opened, [('foo',  'a')])

    def test_with_txlog_threshhold(self):
        import sys
        L = []
        self.config.add_subscriber = lambda func, event: L.append((func, event))
        self.config.registry.settings['zodbconn.uri'] = 'uri'
        self.config.registry.settings['zodbconn.transferlog'] = ''
        self.config.registry.settings['zodbconn.transferlog_threshhold'] = '1'
        self._callFUT(self.config)
        self.assertEqual(len(L), 2)
        self.assertEqual(L[0][0].__name__, 'start')
        self.assertEqual(L[1][0].__name__, 'end')
        self.assertEqual(self.config.registry._transferlog.stream, sys.stdout)
        self.assertEqual(self.config.registry._transferlog.threshhold, 1)

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

class TestTransferLog(unittest.TestCase):
    def _makeOne(self, stream=None, threshhold=None):
        from pyramid_zodbconn import TransferLog
        if stream is None:
            import io
            stream = io.StringIO()
        return TransferLog(stream, threshhold)

    def test_start(self):
        inst = self._makeOne()
        event = DummyZODBEvent()
        inst.start(event, time=FakeTimeModule())
        info = getattr(event.request, inst.key)
        self.assertEqual(info['loads'], 0)
        self.assertEqual(info['stores'], 0)
        self.assertEqual(info['start'], 0)

    def test_end_info_is_None(self):
        inst = self._makeOne()
        event = DummyZODBEvent()
        inst.end(event)
        self.assertEqual(inst.stream.getvalue(), '')

    def test_end_info_is_not_None(self):
        inst = self._makeOne()
        event = DummyZODBEvent()
        begin = 1404321993.792902
        end = 1404321994.792902
        setattr(event.request, inst.key, {'loads':1, 'stores':1, 'start':begin})
        inst.end(event, time=FakeTimeModule(end))
        self.assertEqual(inst.stream.getvalue(),
                         '"2014-07-02 13:26:34", "GET", "", 1.00, -1, -1\n')

    def test_limited_by_threshhold(self):
        inst = self._makeOne(threshhold=5)
        event = DummyZODBEvent()
        begin = 1404321993.792902
        end = 1404321994.792902
        setattr(event.request, inst.key, {'loads':1, 'stores':1, 'start':begin})
        inst.end(event, time=FakeTimeModule(end))
        self.assertEqual(inst.stream.getvalue(), '')

    def test_not_limited_by_threshhold(self):
        inst = self._makeOne(threshhold=1)
        event = DummyZODBEvent()
        begin = 1404321993.792902
        end = 1404321995.792902
        setattr(event.request, inst.key, {'loads':1, 'stores':1, 'start':begin})
        inst.end(event, time=FakeTimeModule(end))
        self.assertEqual(inst.stream.getvalue(),
                         '"2014-07-02 13:26:35", "GET", "", 2.00, -1, -1\n')

class DummyDB:
    def __init__(self, connections=None):
        self.databases = {'unnamed': self}
        self.connection = DummyConnection(connections)
    def open(self):
        return self.connection
    def setActivityMonitor(self, am):
        self.am = am
    def getActivityMonitor(self):
        return getattr(self, 'am', None)

class DummyTransactionManager:
    aborted = False
    def abort(self):
        self.aborted = True

class DummyConnection:
    closed = False

    def __init__(self, connections=None):
        self.transaction_manager = DummyTransactionManager()
        self.connections = connections or {}
        self.transfer_counts = (0, 0)

    def close(self):
        self.closed = True

    def get_connection(self, name):
        return self.connections[name]

    def getTransferCounts(self):
        return self.transfer_counts

class DummyZODBEvent(object):
    def __init__(self):
        self.conn = DummyConnection()
        self.request = testing.DummyRequest()

class FakeTimeModule(object):
    def __init__(self, when=0):
        self.when = when
    def time(self):
        return self.when
