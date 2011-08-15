def zodbconn_tween_factory(handler, registry):
    # db_from_uri injected for testing purposes only

    db = registry.zodb_database
    if db is None:
        return handler

    def zodbconn_tween(request):
        try:
            def get_zodb_connection(request):
                conn = db.open()
                request._zodb_connection = conn
                return conn
            request.get_zodb_connection = get_zodb_connection
            return handler(request)
        finally:
            if hasattr(request, 'get_zodb_connection'):
                del request.get_zodb_connection
            if hasattr(request, '_zodb_connection'):
                conn = request._zodb_connection
                conn.transaction_manager.abort()
                conn.close()

    return zodbconn_tween

