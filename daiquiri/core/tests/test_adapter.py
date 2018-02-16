import logging

from django.conf import settings
from django.test import TestCase

from daiquiri.core.adapter import DatabaseAdapter, DownloadAdapter

logger = logging.getLogger(__name__)


class CoreAdapterTestCase(TestCase):

    def test_fetch_rows_1(self):
        rows = DatabaseAdapter().fetch_rows('daiquiri_data_obs', 'stars', column_names=None, search=None, filters=None)
        self.assertEqual(len(rows), 10)

    def test_fetch_table(self):
        rows = DatabaseAdapter().fetch_table('daiquiri_data_obs', 'stars')
        self.assertEqual(rows['type'], 'table')

    def test_fetch_row(self):
        row = DatabaseAdapter().fetch_row('daiquiri_data_obs', 'stars', column_names=None, search=None, filters={
            'id': '100'
        })
        self.assertEqual(row[1], -12)

    def test_fetch_rows_2(self):
        row = DatabaseAdapter().fetch_rows('daiquiri_data_obs', 'stars')
        self.assertEqual(row[0], (1, 26, -10.54756, 386.3631))

    def test_fetch_stats(self):
        rows = DatabaseAdapter().fetch_stats('daiquiri_data_obs', 'stars')
        self.assertEqual(rows[0], 10000)
        self.assertGreater(rows[1], 400000)

    def test_fetch_columns(self):
        columns = DatabaseAdapter().fetch_columns('daiquiri_archive', 'files')
        self.assertEqual(len(columns), 7)
        self.assertTrue(columns[0]['indexed'])

    def test_fetch_column(self):
        column = DatabaseAdapter().fetch_column('daiquiri_archive', 'files', 'id')
        self.assertTrue(column['datatype'].startswith('char'))

    def test_fetch_column_names(self):
        columns = DatabaseAdapter().fetch_column_names('daiquiri_data_obs', 'stars')
        self.assertEqual(columns[0], 'id')

    def test_count_rows(self):
        row = DatabaseAdapter().count_rows('daiquiri_data_obs', 'stars')
        self.assertEqual(row, 10000)

    def test_download_set_args(self):
        database_config = settings.DATABASES['data']

        adapter = DownloadAdapter()
        adapter.set_args('daiquiri_archive', 'files')

        if database_config['ENGINE'] == 'django.db.backends.mysql':
            # TODO: test
            args_preset = [
                'mysqldump',
                '--compact',
                '--skip-extended-insert',
                '--user=daiquiri_data',
                '--password=daiquiri_data',
                'daiquiri_archive',
                'files'
            ]
        elif database_config['ENGINE'] == 'django.db.backends.postgresql':
            args_preset = [
                'pg_dump',
                '-a',
                '--inserts',
                '--dbname=postgresql://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s' % database_config,
                '--table=daiquiri_archive.files'
            ]

        self.assertEqual(adapter.args, args_preset)
