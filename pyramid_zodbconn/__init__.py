from zodburi import resolve_uri
from ZODB import DB
from pyramid.exceptions import ConfigurationError

def get_connection(request, dbname=None):
    """ Obtain a connection from the database set up as ``zodbconn.uri`` in
    the current configuration.  ``request`` must be a Pyramid request object.
    If you're using named databases, ``dbname`` must be the name of a
    database (e.g. if you've added ``zodbconn.uri.foo`` to the configuration,
    it should be ``foo``).
    """
    # not a tween.  rationale: tweens don't get called until the router accepts
    # a request.  during paster shell, paster ptweens, etc, the router is
    # never invoked

    registry = request.registry
    zodb_conns = getattr(request, '_zodb_conns', None)

    if zodb_conns is None:
        zodb_conns = request._zodb_conns = {}

    conn = zodb_conns.get(dbname)
    if conn is not None:
        return conn

    zodb_dbs = getattr(registry, '_zodb_databases', None)
    if zodb_dbs is None:
        raise ConfigurationError(
            'pyramid_zodbconn not included in configuration')

    db = zodb_dbs.get(dbname)
    if db is None:
        if dbname is None:
            msg = 'No zodbconn.uri defined in Pyramid settings'
        else:
            msg = 'No zodbconn.uri.%s defined in Pyramid settings' % dbname
        raise ConfigurationError(msg)

    zodbconn = db.open()
    zodb_conns[dbname] = zodbconn
    
    def finished(request):
        del request._zodb_conns[dbname]
        zodbconn.transaction_manager.abort()
        zodbconn.close()

    request.add_finished_callback(finished)
    return zodbconn

def db_from_uri(uri, resolve_uri=resolve_uri):
    storage_factory, dbkw = resolve_uri(uri)
    storage = storage_factory()
    return DB(storage, **dbkw)

NAMED = 'zodbconn.uri.'

def get_uris(settings):
    uri = settings.get('zodbconn.uri')
    if uri is not None:
       yield None, uri
    for k, v in settings.items():
        if k.startswith(NAMED):
            yield (k[len(NAMED):], v)

def includeme(config, db_from_uri=db_from_uri):
    """
    This includeme recognizes a ``zodbconn.uri`` setting in your deployment
    settings and creates a ZODB database if it finds one.  ``zodbconn.uri``
    is the database URI or URIs (either a whitespace-delimited string, a
    carriage-return-delimed string or a list of strings).

    It will also recognized *named* database URIs:

        zodbconn.uri.sessions = file:///home/project/var/Data.fs
    
    """
    # db_from_uri in
    databases = config.registry._zodb_databases = {}
    for name, uri in get_uris(config.registry.settings):
        databases[name] = db_from_uri(uri)
        
