"""Neo4j client for medical knowledge graph."""

from contextlib import contextmanager
from typing import Any, Generator

from neo4j import GraphDatabase, Driver, Session, Result

from src.core.config import settings


class Neo4jClient:
    """
    Neo4j database client for medical knowledge graph.

    Provides connection management and query execution
    for the medical ontology graph.
    """

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (default: from settings).
            username: Database username.
            password: Database password.
        """
        self.uri = uri or getattr(settings, "neo4j_uri", "bolt://localhost:7687")
        self.username = username or getattr(settings, "neo4j_user", "neo4j")
        self.password = password or getattr(settings, "neo4j_password", "password")

        self._driver: Driver | None = None

    @property
    def driver(self) -> Driver:
        """Get or create Neo4j driver."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
        return self._driver

    def verify_connectivity(self) -> bool:
        """Verify connection to Neo4j."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    @contextmanager
    def session(self, database: str = "neo4j") -> Generator[Session, None, None]:
        """Get a session context manager."""
        session = self.driver.session(database=database)
        try:
            yield session
        finally:
            session.close()

    def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str = "neo4j",
    ) -> list[dict]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string.
            parameters: Query parameters.
            database: Target database.

        Returns:
            List of result records as dicts.
        """
        with self.session(database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str = "neo4j",
    ) -> Result:
        """
        Execute a write transaction.

        Args:
            query: Cypher query string.
            parameters: Query parameters.
            database: Target database.

        Returns:
            Query result.
        """
        with self.session(database) as session:

            def write_tx(tx):
                return tx.run(query, parameters or {})

            return session.execute_write(write_tx)

    def close(self):
        """Close the driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
