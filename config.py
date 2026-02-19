import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # 1. Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{os.path.join(BASE_DIR, 'agricultural_operations.db')}"
    )
    
    # 2. Open-Meteo Settings
    OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1"
    
    # These match the columns in your WeatherData model
    WEATHER_PARAMS = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "rain",
        "soil_moisture_0_1cm",
        "soil_moisture_1_3cm",
        "soil_moisture_3_9cm"
    ]
    
    # 3. Security (Essential for Prototype 2)
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-farming-key-123")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 Day
    
    # 4. API Settings
    API_V1_PREFIX = "/api/v1"

config = Config()