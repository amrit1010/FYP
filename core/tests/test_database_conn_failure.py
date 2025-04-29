from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings


class TestDatabaseConnectionFailure(TestCase):

    @patch('django.db.backends.utils.CursorWrapper')
    def test_database_connection_failure(self, mock_cursor):
        settings.DATABASES['default']['HOST'] = '69.69.69.69'


        mock_cursor.side_effect = OperationalError("Simulated connection failure")

        db_conn = connections['default']
        with self.assertRaises(OperationalError):
            db_conn.cursor()

        print("Test Failed : Database Unreachable at 69.69.69.69")