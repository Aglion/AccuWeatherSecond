import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
API_KEY = os.getenv('ACCUWEATHER_API_KEY')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_location_key(city_name):
    url = 'https://dataservice.accuweather.com/locations/v1/cities/search'
    params = {
        'apikey': API_KEY,
        'q': city_name,
        'language': 'ru'
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                location_key = data[0]['Key']
                logger.info(f'Ключ локации для {city_name}: {location_key}')
                return location_key
            else:
                logger.warning(f'Локация не найдена для города: {city_name}')
                return None
        else:
            logger.error(f'Ошибка при получении ключа локации для {city_name}: {response.status_code}')
            logger.error(f'Текст ответа: {response.text}')
            return None
    except Exception as e:
        logger.error(f'Произошло исключение при получении ключа локации для {city_name}: {e}')
        return None

def get_weather_forecast(location_key, days=5):
    url = f'https://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}'
    print(API_KEY)
    params = {
        'apikey': API_KEY,
        'language': 'ru',
        'metric': 'true'
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            logger.info(f'Прогноз погоды получен для ключа локации: {location_key} ({days} дней)')
            return data
        else:
            logger.error(f'Ошибка при получении прогноза погоды для ключа локации {location_key}: {response.status_code}')
            logger.error(f'Текст ответа: {response.text}')
            return None
    except Exception as e:
        logger.error(f'Произошло исключение при получении прогноза погоды для ключа локации {location_key}: {e}')
        return None