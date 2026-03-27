import os
import yaml

def expand_env(value):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.getenv(value[2:-1], "")
    return value

class Settings:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        gaia = config["gaia_a08"]
        self.gaia_a08_url = gaia["url"]
        self.gaia_a08_poll_interval = gaia["poll_interval"]

        waqi = config.get("waqi", {})
        self.waqi_enabled = waqi.get("enabled", False)
        self.waqi_url = waqi.get("url", "https://api.waqi.info/feed/here/")
        self.waqi_token = expand_env(waqi.get("token", ""))
        self.waqi_poll_interval = waqi.get("poll_interval", 300)

        db_config = config["database"]
        self.database_type = db_config.get("type", "sqlite")
        if self.database_type == "postgresql":
            pg = db_config["postgres"]
            self.database_url = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['db_name']}"
        else:
            path = db_config.get("sqlite_path", "./air_quality.db")
            self.database_url = f"sqlite:///{path}"
            self.sqlite_path = path

settings = Settings()