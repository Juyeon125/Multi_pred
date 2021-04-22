from app import create_app
from config.app_config import ProductionLevelConfig
from config.db_config import RemoteConfig
from config.run_config import ProductionRunConfig

app = create_app(ProductionLevelConfig, RemoteConfig)

if __name__ == "__main__":
    app.run(**ProductionRunConfig)
