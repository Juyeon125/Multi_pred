from app import create_app
from app import preprocess
from config.app_config import LocalLevelConfig
from config.db_config import LocalConfig
from config.run_config import LocalRunConfig

preprocess.preprocess_deepec()
preprocess.preprocess_ecpred()
preprocess.preprocess_ecami()
preprocess.preprocess_detect_v2()

app = create_app(LocalLevelConfig, LocalConfig)

if __name__ == "__main__":
    app.run(**LocalRunConfig)
