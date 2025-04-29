from django.test import TestCase
from django.db import connections
from django.db.utils import OperationalError

class TestDatabaseConnection(TestCase):

    def test_database_connection_success(self):
        """
        Test if the default database connection is successful.
        """
        db_conn = connections['default']
        try:
            db_conn.cursor()
            connected = True
        except OperationalError:
            connected = False
        self.assertTrue(connected, "Database connection failed.")