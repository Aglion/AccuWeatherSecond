def process_weather_data(weather_data):
    processed_data = {}

    for city, data in weather_data.items():
        dates = []
        temperatures = []
        wind_speeds = []
        precipitation_probs = []

        for day in data.get('DailyForecasts', []):
            dates.append(day.get('Date', '')[:10])
            temperatures.append(day.get('Temperature', {}).get('Maximum', {}).get('Value', None))
            wind_speed = day.get('Day', {}).get('Wind', {}).get('Speed', {}).get('Value', None)
            wind_speeds.append(wind_speed)
            precip_prob = day.get('Day', {}).get('PrecipitationProbability', None)
            precipitation_probs.append(precip_prob)

        processed_data[city] = {
            'dates': dates,
            'temperatures': temperatures,
            'wind_speeds': wind_speeds,
            'precipitation_probs': precipitation_probs
        }

    return processed_data