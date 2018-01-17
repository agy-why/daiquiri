import logging
import re
import six
import warnings

from django.db import OperationalError, ProgrammingError

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


class PostgresAdapter(DatabaseAdapter):

    DATATYPES = {
        'char': {
            'datatype': 'char',
            'arraysize': True
        },
        'varchar': {
            'datatype': 'char',
            'arraysize': True
        },
        'smallint': {
            'datatype': 'unsignedByte',
            'arraysize': False
        },
        'smallint': {
            'datatype': 'short',
            'arraysize': False
        },
        'int': {
            'datatype': 'int',
            'arraysize': False
        },
        'bigint': {
            'datatype': 'long',
            'arraysize': False
        },
        'real': {
            'datatype': 'float',
            'arraysize': False
        },
        'double precision': {
            'datatype': 'double',
            'arraysize': False
        },
        'timestamp': {
            'datatype': 'timestamp',
            'arraysize': False
        }
    }

    def fetch_pid(self):
        return self.connection().connection.thread_id()

    def escape_identifier(self, identifier):
        # escape quates whithin the identifier and quote the string
        return '`%s`' % identifier.replace('"', '"')

    def escape_string(self, string):
        return "'%s'" % string

    def build_query(self, schema_name, table_name, query, timeout, max_records):
        # construct the actual query
        params = {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name),
            'query': query,
            'timeout': timeout,
            'max_records': max_records
        }

        if max_records is not None:
            return 'CREATE TABLE %(schema)s.%(table)s  %(query)s ) LIMIT %(max_records)s;' % params
        else:
            return 'CREATE TABLE %(schema)s.%(table)s  %(query)s );' % params

    def abort_query(self, pid):
        sql = 'select pg_terminate_backend(%(pid)i)' % {'pid': pid}
        self.execute(sql)

    def fetch_stats(self, schema_name, table_name):
        # TODO
        # will be in pg_stat_all_tables, might need a function
        sql = 'SELECT table_rows as nrows, data_length + index_length AS size FROM "pg_stat_all_tables" WHERE "table_schema" = %s AND table_name = %s;'
        return self.fetchone(sql, (schema_name, table_name))

    def count_rows(self, schema_name, table_name, column_names=None, search=None, filters=None):
        # if no column names are provided get all column_names from the table
        if not column_names:
            column_names= self.fetch_column_names(schema_name, table_name)

        # create a list of escaped columns
        escaped_column_names = [self.escape_identifier(column_name) for column_name in column_names]

        # prepare sql string
        sql = 'SELECT COUNT(*) FROM %(schema)s.%(table)s' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name)
        }
        sql_args = []

        # process filtering
        sql, sql_args = self._process_filtering(sql, sql_args, search, filters, escaped_column_names)

        return self.fetchone(sql, args=sql_args)[0]

    def fetch_row(self, schema_name, table_name, column_names=None, search=None, filters=None):

        # if no column names are provided get all column_names from the table
        if not column_names:
            column_names = self.fetch_column_names(schema_name, table_name)

        # create a list of escaped columns
        escaped_column_names = [self.escape_identifier(column_name) for column_name in column_names]

        # prepare sql string
        sql = 'SELECT %(columns)s FROM %(schema)s.%(table)s' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name),
            'columns': ', '.join(escaped_column_names)
        }
        sql_args = []

        # process filtering
        sql, sql_args = self._process_filtering(sql, sql_args, search, filters, escaped_column_names)

        return self.fetchone(sql, args=sql_args)

    def fetch_dict(self, schema_name, table_name, column_names=None, search=None, filters=None):

        # if no column names are provided get all column_names from the table
        if not column_names:
            column_names = self.fetch_column_names(schema_name, table_name)

        row = self.fetch_row(schema_name, table_name, column_names, search, filters)

        if row:
            return {
                column_name: value for column_name, value in zip(column_names, row)
            }
        else:
            return {}

    def fetch_rows(self, schema_name, table_name, column_names=None, ordering=None, page=1, page_size=10, search=None, filters=None):

        # if no column names are provided get all column_names from the table
        if not column_names:
            column_names = self.fetch_column_names(schema_name, table_name)

        # create a list of escaped columns
        escaped_column_names = [self.escape_identifier(column_name) for column_name in column_names]

        # init sql string and sql_args list
        sql = 'SELECT %(columns)s FROM %(schema)s.%(table)s' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name),
            'columns': ', '.join(escaped_column_names)
        }
        sql_args = []

        # process filtering
        sql, sql_args = self._process_filtering(sql, sql_args, search, filters, escaped_column_names)

        # process ordering
        sql = self._process_ordering(sql, ordering, escaped_column_names)

        # process page and page_size
        if page_size > 0:
            sql += ' LIMIT %(limit)s OFFSET %(offset)s' % {
                'limit': page_size,
                'offset': (int(page) - 1) * int(page_size)
            }

        return self.fetchall(sql, args=sql_args)

    def _process_filtering(self, sql, sql_args, search, filters, escaped_column_names):
        # prepare lists for the WHERE statements
        where_stmts = []
        where_args = []

        if search:
            # append a OR condition fo every column
            search_stmts = []
            search_args = []
            for escaped_column_name in escaped_column_names:
                search_stmts.append(escaped_column_name + ' LIKE %s')
                search_args.append('%' + search + '%')

            if search_stmts:
                where_stmts.append('(' + ' OR '.join(search_stmts) + ')')
                where_args += search_args

        if filters:
            for column_name, column_filter in filters.items():
                # escpae the column_name for this column
                escaped_column_name = self.escape_identifier(column_name)

                # check if the filter is a list or a string
                if isinstance(column_filter, six.string_types):
                    filter_list = [column_filter]
                elif isinstance(column_filter, list):
                    filter_list = column_filter
                else:
                    raise RuntimeError('Unsupported filter for column "%s"' % column_name)

                # append a OR condition fo every entry in the list
                filter_stmts = []
                filter_args = []
                for filter_string in filter_list:
                    filter_stmts.append(escaped_column_name + ' = %s')
                    filter_args.append(filter_string)

                if filter_stmts:
                    where_stmts.append('(' + ' OR '.join(filter_stmts) + ')')
                    where_args += filter_args

        # connect the where statements with AND and append to the sql string
        if where_stmts:
            sql += ' WHERE ' + ' AND '.join(where_stmts)
            sql_args += where_args

        return sql, sql_args

    def _process_ordering(self, sql, ordering, escaped_column_names):
        if ordering:
            if ordering.startswith('-'):
                escaped_ordering_column, ordering_direction = self.escape_identifier(ordering[1:]), 'DESC'
            else:
                escaped_ordering_column, ordering_direction = self.escape_identifier(ordering), 'ASC'

            if escaped_ordering_column in escaped_column_names:
                sql += ' ORDER BY %(column)s %(direction)s' % {
                    'column': escaped_ordering_column,
                    'direction': ordering_direction
                }

        return sql

    def create_user_schema_if_not_exists(self, schema_name):
        # escape input
        escaped_schema_name = self.escape_identifier(schema_name)

        # prepare sql string
        sql = 'CREATE SCHEMA IF NOT EXISTS %(schema)s' % {
            'schema': escaped_schema_name
        }

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.execute(sql)

    def create_user_schema_if_not_exists(self, schema_name):
        # escape input
        escaped_schema_name = self.escape_identifier(schema_name)

        # prepare sql string
        sql = 'CREATE schema IF NOT EXISTS %(schema)s' % {
            'schema': escaped_schema_name
        }

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.execute(sql)



    def fetch_tables(self, schema_name):
        # escape input
        escaped_schema_name = self.escape_identifier(schema_name)

        # prepare sql string
        # TODO: test 
         sql = 'SELECT table_name, table_type FROM information_schema.tables where table_schema = %(schema)s'{
            'schema': escaped_schema_name
        }

        # execute query
        try:
            rows = self.fetchall(sql)
        except OperationalError as e:
            logger.error('Could not fetch from %s (%s)' % (schema_name, e))
            return []
        else:
            return [{
                'name': row[0],
                'type': 'view' if row[1] == 'VIEW' else 'table'
            } for row in rows]

    def fetch_table(self, schema_name, table_name):
        # prepare sql string
        # TODO: to test
        sql = 'SELECT table_name, table_type FROM information_schema.tables where table_schema = %(schema)s LIKE %(table)s' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_string(table_name)
        }

        # execute query
        try:
            row = self.fetchone(sql)
        except OperationalError as e:
            logger.error('Could not fetch %s.%s (%s)' % (schema_name, table_name, e))
            return {}
        else:
            return {
                'name': row[0],
                'type': 'view' if row[1] == 'VIEW' else 'table'
            }

    def rename_table(self, schema_name, table_name, new_table_name):
        # TODO: test
        sql = 'ALTER TABLE %(schema)s.%(table)s RENAME TO %(schema)s.%(new_table)s;' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name),
            'new_table': self.escape_identifier(new_table_name)
        }

        self.execute(sql)

    def drop_table(self, schema_name, table_name):
        # TODO: test
        sql = 'DROP TABLE IF EXISTS %(schema)s.%(table)s;' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name)
        }

        self.execute(sql)

    def fetch_columns(self, schema_name, table_name):
        # prepare sql string
        # TODO: get index
        # this will get you column names and types
        # sql = 'SELECT column_name, data_type  FROM information_schema.tables where table_schema = %(schema)s LIKE %(table)s' % 
        # and this will get you the indicies
        # SELECT * FROM pg_indexes WHERE tablename = 'images';
        # 2 queries needed, view?
        sql = 'SHOW FULL COLUMNS FROM %(schema)s.%(table)s;' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name)
        }

        # execute query
        try:
            rows = self.fetchall(sql)
        except ProgrammingError as e:
            logger.error('Could not fetch from %s.%s (%s)' % (schema_name, table_name, e))
            return []
        else:
            column_metadata = []
            for row in rows:
                datatype, arraysize = self.convert_datatype(row[1])

                column_metadata.append({
                    'name': row[0],
                    'datatype': datatype,
                    'arraysize': arraysize,
                    'indexed': bool(row[4])
                })

            return column_metadata

    def fetch_column(self, schema_name, table_name, column_name):
        # prepare sql string
        # TODO: 
        # this will get you column names and types
        # sql = 'SELECT column_name, data_type  FROM information_schema.tables where table_schema = %(schema)s LIKE %(table)s' % 
        sql = 'SHOW FULL COLUMNS FROM %(schema)s.%(table)s WHERE `Field` = %(column)s' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name),
            'column': self.escape_string(column_name)
        }

        # execute query
        try:
            row = self.fetchone(sql)
        except ProgrammingError as e:
            logger.error('Could not fetch %s.%s.%s (%s)' % (schema_name, table_name, column_name, e))
            return {}
        else:
            return {
                'name': row[0],
                'datatype': row[1],
                'indexed': bool(row[4])
            }

    def fetch_column_names(self, schema_name, table_name):
        # prepare sql string
        # TODO: 
        # this will get you column names and types
        # sql = 'SELECT column_name, data_type  FROM information_schema.tables where table_schema = %(schema)s LIKE %(table)s' % 

        sql = 'SHOW COLUMNS FROM %(schema)s.%(table)s' % {
            'schema': self.escape_identifier(schema_name),
            'table': self.escape_identifier(table_name),
        }
        return [column[0] for column in self.fetchall(sql)]

    def convert_datatype(self, datatype_string):
        result = re.match('([a-z]+)\(*(\d*)\)*', datatype_string)

        if result:
            native_datatype = result.group(1)

            try:
                native_arraysize = int(result.group(2))
            except ValueError:
                native_arraysize = None

            if native_datatype in self.DATATYPES:
                datatype = self.DATATYPES[native_datatype]['datatype']

                if self.DATATYPES[native_datatype]['arraysize']:
                    arraysize = native_arraysize
                else:
                    arraysize = None

                return datatype, arraysize
            else:
                return native_datatype, native_arraysize
        else:
            return datatype_string, None
