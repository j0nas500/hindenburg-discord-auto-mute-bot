from abc import ABC

import mariadb


class DbConnection(ABC):

    def __init__(self, user: str, password: str, host: str, port: int, database: str):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database

        try:
            conn = mariadb.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=database
            )
            conn.auto_reconnect = True
            cursor = conn.cursor(buffered=True)

            print("Connected to the Database")
        except mariadb.Error as e:
            print("Error at:")
            print(e)
            exit()

        self.conn = conn
        self.cursor = cursor

    def execute(self, query):
        try:
            self.cursor.execute(query)
            self.conn.commit()
            # cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error: {e}")
            return str(e)

    def execute_list(self, query):
        try:
            self.cursor.execute(query)
            self.conn.commit()
            return self.cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error: {e}")
            return str(e)

    def execute_rows(self, query):
        try:
            self.cursor.execute(query)
            rows = self.cursor.rowcount
            self.conn.commit()
            return rows
        except mariadb.Error as e:
            print(f"Error: {e}")
            return str(e)

    def close(self):
        self.cursor.close()
        self.conn.close()
