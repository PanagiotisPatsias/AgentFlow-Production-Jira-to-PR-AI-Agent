from agentflow.checkpointing.postgres import setup_checkpoint_database
from agentflow.core.config import Setting

setting = Setting()

setup_checkpoint_database(setting.LANGGRAPH_DATABASE_URL.get_secret_value())

print("LangGraph checkpoint database initialized")