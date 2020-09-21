import pluggy

hookspec = pluggy.HookspecMarker("exercise_plotter")


@hookspec
def import_data_from_device(db_handle):
    """Provides a handle to the backend database to facilitate adding data

    The handle has been initiated as following:

    with session_scope() as session:
        db = DBManager(session)
        import_data_from_device(db)

    See docs for exercise_plotter.backend.database_manager:DBManager on how to
    add new data

    """
