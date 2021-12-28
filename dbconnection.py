from psycopg2 import connect, DatabaseError
from os import environ


class DBConnection:
    """
    Handles database operations
    """
    def __init__(self):
        self.__conn = None

    def connect(self):
        db_name = environ["DATABASE_NAME"]
        db_host = environ['DATABASE_HOST']
        db_user = environ['DATABASE_USER']
        db_password = environ['DATABASE_PASSWORD']
        self.__conn = connect(host=db_host, user=db_user,
                              database=db_name, password=db_password)

    def __create_conditions(self, **kwargs):
        result = ''
        if kwargs:
            keys = list(kwargs.keys())
            values = list(kwargs.values())
            result += f'WHERE {keys[0]} = \'{values[0]}\''
            for i in range(1, len(kwargs)):
                result += f' AND {keys[i]} = \'{values[i]}\''
        return result

    def record_exists(self, table_name, col_name, **condition_values):
        if self.__conn is None:
            raise DatabaseError('not connected to database')
        cursor = self.__conn.cursor()
        conditions = self.__create_conditions(**condition_values)
        cursor.execute(f'SELECT {col_name} FROM {table_name} {conditions};')
        result = cursor.fetchall()
        if not result or result[0][0] is None:
            return False
        return True

    def select(self, table_name, cols, **condition_values):
        if self.__conn is None:
            raise DatabaseError('not connected to database')
        cursor = self.__conn.cursor()
        columns = ', '.join(cols)
        conditions = self.__create_conditions(**condition_values)
        cursor.execute(f'SELECT {columns} FROM {table_name} {conditions}')
        return cursor.fetchall()

    def insert(self, table_name, cols, vals):
        if self.__conn is None:
            raise DatabaseError('not connected to database')
        cursor = self.__conn.cursor()
        columns = ', '.join(cols)
        values = ', '.join([f'\'{val}\'' for val in vals])
        cursor.execute(
            f'INSERT INTO {table_name} ({columns}) VALUES ({values});')
        self.__conn.commit()

    def update(self, table_name, col_name, value, **condition_values):
        if self.__conn is None:
            raise DatabaseError('not connected to database')
        cursor = self.__conn.cursor()
        conditions = self.__create_conditions(**condition_values)    
        cursor.execute(
            f'UPDATE {table_name} SET {col_name} = \'{value}\' {conditions};')
        self.__conn.commit()

    def delete(self, table_name, **condition_values):
        if self.__conn is None:
            raise DatabaseError('not connected to database')
        cursor = self.__conn.cursor()
        conditions = self.__create_conditions(**condition_values)
        cursor.execute(f'DELETE FROM {table_name} {conditions};')
        self.__conn.commit()

    def disconnect(self):
        self.__conn.close()
