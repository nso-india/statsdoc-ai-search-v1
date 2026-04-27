import pandas as pd
from vanna.openai import OpenAI_Chat
from vanna.ollama import Ollama
from vanna.anthropic import Anthropic_Chat
from openai import AzureOpenAI
from vanna.qdrant import Qdrant_VectorStore

from django.conf import settings
from qdrant_adapter.qdrant_adapter import init_connection


def get_universal_sql_prompt(table_names=None, document_context=None):
    base_prompt = (
        "You are a PostgreSQL expert. You must respond with ONLY SQL queries - nothing else.\n\n"
        "CRITICAL: Your response must contain ONLY the SQL query. No explanations, no text, no comments, no markdown.\n\n"
        "RULES:\n"
        "1. Return ONLY valid PostgreSQL SQL\n"
        "2. No explanations before, after, or around the query\n"
        "3. No markdown code blocks (```sql)\n"
        "4. No comments unless for intermediate_sql\n"
        "5. Use provided schema tables and columns only\n"
        "6. Use appropriate JOINs for multiple tables\n"
        "7. Use WHERE clauses for filtering\n"
        "8. Use aggregate functions (SUM, COUNT, etc.) when needed\n\n"
    )

    if table_names:
        table_focus = f"FOCUS ON THESE TABLES: {', '.join(table_names)}\nPRIORITY: Use the tables mentioned above as they were identified from document analysis.\n\n"
        base_prompt += table_focus

    base_prompt += (
        "INTERMEDIATE QUERIES:\n"
        "If you need to explore data first, respond with ONLY:\n"
        "--intermediate_sql\n"
        "SELECT DISTINCT column1, column2 FROM table_name LIMIT 10;\n\n"
        "EXAMPLES OF CORRECT RESPONSES:\n"
        "SELECT * FROM users WHERE age > 25;\n\n"
        "SELECT COUNT(*) FROM orders o JOIN customers c ON o.customer_id = c.id;\n\n"
        "--intermediate_sql\n"
        "SELECT DISTINCT category FROM products LIMIT 5;\n\n"
        "Remember: ONLY SQL queries. No other text allowed."
    )

    return base_prompt


class VannaAdapterBase(Qdrant_VectorStore):
    def __init__(self, config=None):
        Qdrant_VectorStore.__init__(self, config=config)

    def train_on_db(self):
        if not self.run_sql_is_set:
            raise ValueError(
                "Database connection is not set. Please connect to the database before training."
            )
        table_names = self.run_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        for table in table_names["table_name"]:
            df_information_schema = self.run_sql(
                f"SELECT * from INFORMATION_SCHEMA.COLUMNS where table_name='{table}';"
            )
            table_df = self.run_sql(f"SELECT * FROM {table} limit 5;")
            ddl_query = pd.io.sql.get_schema(table_df.reset_index(), name=table)
            plan = self.get_training_plan_generic(df_information_schema)
            self.train(plan=plan)
            self.train(ddl=ddl_query)

    def train_on_table(self, table):
        if not self.run_sql_is_set:
            raise ValueError(
                "Database connection is not set. Please connect to the database before training."
            )
        df_information_schema = self.run_sql(
            f"SELECT * from INFORMATION_SCHEMA.COLUMNS where table_name='{table}';"
        )
        table_df = self.run_sql(f"SELECT * FROM {table} limit 5;")
        ddl_query = pd.io.sql.get_schema(table_df.reset_index(), name=table)
        plan = self.get_training_plan_generic(df_information_schema)
        self.train(plan=plan)
        self.train(ddl=ddl_query)


class VannaAdapterOpenAI(VannaAdapterBase, OpenAI_Chat):
    def __init__(self, config=None):
        azure_client = AzureOpenAI(
            api_key=settings.LLM_API_KEY,
            api_version=settings.LLM_API_VERSION,
            azure_endpoint=settings.LLM_API_URL,
        )
        VannaAdapterBase.__init__(self, config=config)
        OpenAI_Chat.__init__(self, client=azure_client, config=config)


class VannaAdapterOllama(VannaAdapterBase, Ollama):
    def __init__(self, config=None):
        VannaAdapterBase.__init__(self, config=config)
        Ollama.__init__(self, config=config)


class VannaAdapterClaude(VannaAdapterBase, Anthropic_Chat):
    def __init__(self, config=None):
        VannaAdapterBase.__init__(self, config=config)
        Anthropic_Chat.__init__(self, config=config)


def init_vanna_adapter(table_names=None):
    qdrant_client = init_connection()

    initial_prompt = get_universal_sql_prompt(table_names)

    if settings.SQL_QUERY_LLM_TYPE == "openai":
        vn = VannaAdapterOpenAI(
            config={
                "client": qdrant_client,
                "model": settings.SQL_QUERY_LLM_MODEL_NAME,
                "initial_prompt": initial_prompt,
            }
        )
    elif settings.SQL_QUERY_LLM_TYPE == "ollama":
        vn = VannaAdapterOllama(
            config={
                "client": qdrant_client, 
                "model": settings.SQL_QUERY_LLM_MODEL_NAME,
                "initial_prompt": initial_prompt,
            }
        )
    elif settings.SQL_QUERY_LLM_TYPE == "claude":
        vn = VannaAdapterClaude(
            config={
                "client": qdrant_client,
                "api_key": settings.ANTHROPIC_API_KEY,
                "model": settings.SQL_QUERY_LLM_MODEL_NAME,
                "initial_prompt": initial_prompt,
            }
        )
    else:
        raise ValueError(f"Unsupported SQL_QUERY_LLM_TYPE: {settings.SQL_QUERY_LLM_TYPE}")

    vn.connect_to_postgres(
        host=settings.FILE_TABLE_DB_HOST,
        port=settings.FILE_TABLE_DB_PORT,
        user=settings.FILE_TABLE_POSTGRES_USER,
        password=settings.FILE_TABLE_POSTGRES_PASSWORD,
        dbname=settings.FILE_TABLE_POSTGRES_DB,
    )

    vn.allow_llm_to_see_data = True

    if hasattr(vn, 'config') and vn.config is not None:
        vn.config['allow_llm_to_see_data'] = True
    elif hasattr(vn, 'config'):
        vn.config = {'allow_llm_to_see_data': True}

    return vn
