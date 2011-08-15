
import unittest

class TestDBFromURI(unittest.TestCase):
    def setUp(self):
        from pyramid_zodbconn.resolvers import RESOLVERS
        self.root = DummyRoot()
        self.db = DummyDB(self.root, 'foo')
        def dbfactory():
            return self.db
        RESOLVERS['foo'] = lambda *arg: ('key', 'arg', 'kw', dbfactory)
        def addon_dbfactory():
            return DummyDB(DummyRoot(), 'addon')
        RESOLVERS['addon'] = lambda *arg: ('key', 'arg', 'kw', addon_dbfactory)

    def tearDown(self):
        from pyramid_zodbconn.resolvers import RESOLVERS
        del RESOLVERS['foo']
        del RESOLVERS['addon']

    def _callFUT(self, uri):
        from pyramid_zodbconn.uri import db_from_uri
        return db_from_uri(uri)

    def failUnless(self, expr, msg=None):
        # silence stupid 2.7 stdlib deprecation
        if not expr: #pragma NO COVERAGE
            raise self.failureException, msg

    def test_single_database(self):
        db = self._callFUT('foo://bar.baz')
        self.assertEqual(db.database_name, 'foo')

    def test_multiple_databases_via_whitespace(self):
        db = self._callFUT(' foo://bar.baz  addon:// ')
        self.assertEqual(db.database_name, 'foo')
        self.failUnless('addon' in db.databases)
        self.failUnless('foo' in db.databases)
        self.assertEqual(db.databases,
            db.databases['addon'].databases)

    def test_multiple_databases_via_list(self):
        db = self._callFUT(['foo://bar.baz', 'addon://'])
        self.assertEqual(db.database_name, 'foo')
        self.failUnless('addon' in db.databases)
        self.failUnless('foo' in db.databases)
        self.assertEqual(db.databases,
            db.databases['addon'].databases)

    def test_disallow_duplicate_database_name(self):
        self.assertRaises(
            ValueError, self._callFUT, 'foo://bar.baz foo://bar.baz')


class TestDBFactoryFromURI(unittest.TestCase):
    def setUp(self):
        from pyramid_zodbconn.resolvers import RESOLVERS
        RESOLVERS['foo'] = lambda *arg: ('key', 'arg', 'kw', 'factory')

    def tearDown(self):
        from pyramid_zodbconn.resolvers import RESOLVERS
        del RESOLVERS['foo']

    def _getFUT(self):
        from pyramid_zodbconn.uri import dbfactory_from_uri
        return dbfactory_from_uri

    def test_it(self):
        dbfactory_from_uri = self._getFUT()
        self.assertEqual(dbfactory_from_uri('foo://abc'), 'factory')
        self.assertRaises(ValueError, dbfactory_from_uri, 'bar://abc')


class DummyDB:
    def __init__(self, rootob, database_name):
        self.conn = DummyConn(rootob)
        self.database_name = database_name
        self.databases = {database_name: self}

class DummyConn:
    closed = False

    def __init__(self, rootob):
        self.rootob = rootob

class DummyRoot:
    pass
