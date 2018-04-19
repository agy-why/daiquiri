from django.contrib.auth.models import User
from django.test import TestCase

from daiquiri.query.utils import check_permissions


class QueryPermissionsTestCase(TestCase):

    fixtures = (
        'auth.json',
        'metadata.json'
    )

    users = (
        ('admin', 'admin'),
        ('user', 'user'),
        ('anonymous', None),
    )

    def test_columns(self):
        user = User.objects.get(username='admin')
        keywords = []
        tables = [('daiquiri_data_obs', 'stars')]
        columns = [
            ('daiquiri_data_obs', 'stars', 'ra'),
            ('daiquiri_data_obs', 'stars', 'dec')
        ]
        functions = []

        result = check_permissions(user, keywords, tables, columns, functions)

        self.assertEqual(result, [])

    def test_columns_not_found(self):
        user = User.objects.get(username='admin')
        keywords = []
        tables = [('daiquiri_data_obs', 'stars')]
        columns = [
            ('daiquiri_data_obs', 'stars', 'ra'),
            ('daiquiri_data_obs', 'stars', 'not_found')
        ]
        functions = []

        result = check_permissions(user, keywords, tables, columns, functions)

        self.assertEqual(result, ['Column not_found not found.'])

    def test_alias(self):
        user = User.objects.get(username='admin')
        keywords = []
        tables = [('daiquiri_data_obs', 'stars')]
        columns = [
            ('daiquiri_data_obs', 'stars', 'ra'),
            ('daiquiri_data_obs', 'stars', 'dec'),
            (None, None, 'alias')
        ]
        functions = []

        result = check_permissions(user, keywords, tables, columns, functions)

        self.assertEqual(result, [])
