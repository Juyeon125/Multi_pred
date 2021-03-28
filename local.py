from app import create_app
from app import preprocess
from config.app_config import LocalLevelConfig
from config.db_config import LocalConfig
from config.run_config import LocalRunConfig

app = create_app(LocalLevelConfig, LocalConfig)

if __name__ == "__main__":
    # preprocess.preprocess_deepec()

    app.run(**LocalRunConfig)