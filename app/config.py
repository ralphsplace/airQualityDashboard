import yaml
import os

class Settings:
    def __init__(self):
        # Determine config path (default to config.yaml in root)
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Polling Settings
        self.poll_url = config['polling']['url']
        self.poll_interval = config['polling']['interval_seconds']

        # Database Settings
        db_config = config['database']
        self.db_type = db_config.get('type', 'sqlite')

        if self.db_type == 'postgresql':
            pg = db_config['postgres']
            # Construct Postgres connection string
            self.database_url = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['db_name']}"
        else:
            # Construct SQLite connection string
            path = db_config.get('sqlite_path', './air_quality.db')
            self.database_url = f"sqlite:///{path}"

# Create a single instance to be imported everywhere
settings = Settings()