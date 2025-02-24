import dataclasses
import os

import pyodbc
import pydantic

from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope

@pydantic.dataclasses.dataclass
class MssqlProviderAuthConfig:
    host: str = dataclasses.field(
        metadata={
            "required": True,
            "description": "MSSQL hostname"
        }
    )
    username: str = dataclasses.field(
      metadata={
        "required": True,
        "description": "MSSQL username"
      }
    )
    password: str = dataclasses.field(
      metadata={
        "required": True,
        "description": "MSSQL password",
        "sensitive": True
      }
    )
    database: str = dataclasses.field(
      metadata={
        "required": True,
        "description": "MSSQL database name"
      }
    )

class MssqlProvider(BaseProvider):
    """
    Enrich alerts with data from MSSQL.
    """

    PROVIDER_DISPLAY_NAME = "MSSQL"
    PROVIDER_CATEGORY = ["Database"]

    PROVIDER_SCOPES = [
        ProviderScope(
            name="connect_to_server",
            description="The user can connect to the server",
            mandatory=True,
            alias="Connect to the server"
        )
    ]

    def __init__(
            self, context_manager: ContextManager, provider_id: str, config: ProviderConfig
    ):
        super().__init__(context_manager, provider_id, config)
        self.client = None

    def validate_scopes(self):
        """
        Validates that the user has the required scopes to use the provider.
        """
        try:
            conn = self._generate_conn()
            cursor = conn.cursor()
            sql_query = "SELECT 1"

            cursor.execute(sql_query)
            cursor.close()
            conn.close()
            
            scopes = {
                "connect_to_server": True,
            }
        except Exception as e:
            self.logger.exception("Error validating scopes")
            scopes = {
                "connect_to_server": str(e),
            }
        return scopes
    
    def _generate_conn(self):
        """
        Generate a connection to the MSSQL server.
        """
        connectionString = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={self.authentication_config.host};DATABASE={self.authentication_config.database};UID={self.authentication_config.username};PWD={self.authentication_config.password};TrustServerCertificate=yes;"

        return pyodbc.connect(connectionString)
    
    def dispose(self):
        try:
            self.client.close()
            self.conn.close()
        except Exception:
            self.logger.exception("Error closing MSSQL connection")

    def validate_config(self):
        """
        Validates required configuration for MySQL's provider.
        """
        self.authentication_config = MssqlProviderAuthConfig(
            **self.config.authentication
        )

    def _query(self, query="") -> list:
        """
        Execute a query on the MSSQL server.
        """
        conn = self._generate_conn()
        cursor = conn.cursor()

        cursor.execute(query)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if len(results) >= 1:
            return [list(record) for record in results]
        else:
            self.logger.warning("No results found for query: %s", query)
            raise ValueError(f"Query {query} returned no rows")
        
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
    context_manager = ContextManager(
        tenant_id="singletenant",
        workflow_id="test",
    )

    config = ProviderConfig(
        description="MSSQL provider",
        authentication={
            "host": os.getenv("MSSQL_HOST"),
            "username": os.getenv("MSSQL_USERNAME"),
            "password": os.getenv("MSSQL_PASSWORD"),
            "database": os.getenv("MSSQL_DATABASE")
        }
    )

    mssql_provider = MssqlProvider(
        context_manager,
        "mssql",
        config
    )

    result = mssql_provider._query("SELECT * FROM dbo.Inventory")
    print(result)