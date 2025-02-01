import psycopg2
import os
from psycopg2 import sql


class ConnectionManager:
    def __init__(self):
        self.connection = None

    def get_cursor(
        self,
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ):
        """
        Returns a cursor to the database with autocommit enabled
        """
        # Connect to the Postgres server
        self.connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )

        # Enable autocommit mode
        self.connection.autocommit = True
        # Create a cursor object
        return self.connection.cursor()

    def close_connection(self, cursor):
        """
        Closes the cursor and connection
        """
        cursor.close()
        self.connection.close()


def create_user_and_database():
    try:
        # Fetch environment variables
        postgres_admin_host = os.environ["POSTGRES_HOST"]
        postgres_admin_port = os.environ["POSTGRES_PORT"]
        postgres_admin_database = os.environ["POSTGRES_DB"]
        postgres_admin_username = os.environ["POSTGRES_USER"]
        postgres_admin_password = os.environ["POSTGRES_PASSWORD"]
        app_host = os.environ["TODO_APP_HOST"]
        app_port = os.environ["TODO_APP_PORT"]
        app_database = os.environ["TODO_APP_DB"]
        app_user = os.environ["TODO_APP_DB_USER"]
        app_user_password = os.environ["TODO_APP_DB_PASSWORD"]
        keycloak_schema = os.environ["KC_DB_SCHEMA"]
        app_schema = os.environ["TODO_APP_SCHEMA"]

        # Create a connection manager
        cm = ConnectionManager()

        # Connect to the Postgres server
        cur = cm.get_cursor(
            host=postgres_admin_host,
            port=postgres_admin_port,
            database=postgres_admin_database,
            user=postgres_admin_username,
            password=postgres_admin_password,
        )

        # Check if the user exists
        cur.execute(sql.SQL("SELECT 1 FROM pg_roles WHERE rolname = %s"), (app_user,))
        if cur.fetchone() is None:
            print(f"User {app_user} does not exist, creating...")
            query_list = [
                sql.SQL(
                    "CREATE ROLE {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN NOREPLICATION NOBYPASSRLS PASSWORD {}"
                ).format(sql.Identifier(app_user), sql.Literal(app_user_password)),
                sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(
                    sql.Identifier(app_user)
                ),
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}"
                ).format(sql.Identifier(app_user)),
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLES TO {}"
                ).format(sql.Identifier(app_user)),
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {}"
                ).format(sql.Identifier(app_user)),
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}"
                ).format(sql.Identifier(app_user)),
            ]

            for query in query_list:
                cur.execute(query)
        else:
            print(f"User {app_user} already exists, skipping...")

        # Check if the database exists
        cur.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), (app_database,)
        )
        if cur.fetchone() is None:
            # Create the new database
            print(f"Database {app_database} does not exist, creating...")
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(app_database), sql.Identifier(app_user)
                )
            )
        else:
            print(f"Database {app_database} already exists, skipping...")

        # Close the cursor and connection
        cm.close_connection(cur)

        # Connect to the app db server
        app_cur = cm.get_cursor(
            host=app_host,
            port=app_port,
            database=app_database,
            user=app_user,
            password=app_user_password,
        )

        schema_list = [keycloak_schema, app_schema]
        for schema in schema_list:
            # Check if schema exists
            app_cur.execute(
                sql.SQL("SELECT 1 FROM pg_namespace WHERE nspname = %s"), (schema,)
            )
            if app_cur.fetchone() is None:
                # Create schema
                print(f"Schema {schema} does not exist, creating...")
                app_cur.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}").format(
                        sql.Identifier(schema), sql.Identifier(app_user)
                    )
                )
            else:
                print(f"Schema {schema} already exists, skipping...")

        # Close the cursor and connection
        cm.close_connection(app_cur)

    except psycopg2.Error as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    create_user_and_database()
