from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def create_postgres_checkpointer(
    database_url: str,
) -> tuple[PostgresSaver, ConnectionPool]:

    pool = ConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=5,
        timeout=30,
        open=True,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )
    pool.wait(timeout=30)

    checkpointer = PostgresSaver(pool)

    return checkpointer, pool


def setup_checkpoint_database(database_url: str) -> None:
    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        checkpointer.setup()
