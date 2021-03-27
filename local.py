from app import create_app
from config.app_config import LocalLevelConfig
from config.db_config import LocalConfig
from config.run_config import LocalRunConfig

app = create_app(LocalLevelConfig, LocalConfig)

if __name__ == "__main__":
    app.run(**LocalRunConfig)
