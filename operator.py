import requests
from flask import Flask, request, render_template
from requests import Timeout, HTTPError

app = Flask(__name__)

API_KEY = "c7119797242e1b1e6ec707df8602861f"
BASE_URL_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"


def analyze_weather(temp, wind, rain):
    if temp is None:
        return "Невозможно определить погодные условия."

    feedback = []

    if temp < 0:
        feedback.append("На улице холодно. Одевайтесь теплее!")
    elif 0 <= temp < 10:
        feedback.append("Прохладная погода. Захватите куртку.")
    elif temp > 35:
        feedback.append("Очень жарко! Будьте осторожны на солнце.")

    if wind > 10:
        feedback.append("Сильный ветер. Подумайте о защите от ветра.")
    if rain > 0:
        feedback.append("Идёт дождь. Возьмите зонтик!")

    if not feedback:
        feedback.append("Отличная погода для прогулок!")

    return " ".join(feedback)


def fetch_weather_data(cities, interval):
    results = []

    for city in cities:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric',
        }

        try:
            response = requests.get(BASE_URL_FORECAST, params=params, timeout=5)
            response.raise_for_status()

            forecast_data = response.json()
            forecast = forecast_data['list'][int(interval) - 1]

            city_info = {
                'City': city,
                'Temperature': forecast['main']['temp'],
                'Humidity': forecast['main']['humidity'],
                'Wind_Speed': forecast['wind']['speed'],
                'Rain_Probability': forecast.get('rain', {}).get('3h', 0),
                'Description': forecast['weather'][0]['description'].capitalize()
            }
            results.append(city_info)

        except ConnectionError:
            results.append({
                'City': city,
                'Description': "Не удалось подключиться к серверу. Проверьте подключение."
            })
        except Timeout:
            results.append({
                'City': city,
                'Description': "Сервер не отвечает. Попробуйте позже."
            })
        except HTTPError as e:
            error_message = "Город не найден. Проверьте название." if response.status_code == 404 else f"Ошибка сервера: {response.status_code}"
            results.append({
                'City': city,
                'Description': error_message
            })
        except Exception as e:
            results.append({
                'City': city,
                'Description': f"Произошла непредвиденная ошибка: {str(e)}"
            })

    return results

@app.route("/", methods=['GET', 'POST'])
def index():
    results = []
    error_message = None

    if request.method == 'POST':
        start_city = request.form.get('start_city')
        end_city = request.form.get('end_city')
        interval = request.form.get('interval', '1')

        if not start_city or not end_city:
            error_message = "Пожалуйста, укажите оба города."
        else:
            weather_data = fetch_weather_data([start_city, end_city], interval)
            for city in weather_data:
                results.append({
                    'City': city.get('City', 'Неизвестно'),
                    'Temperature': city.get('Temperature', 'Нет данных'),
                    'Humidity': city.get('Humidity', 'Нет данных'),
                    'Wind_Speed': city.get('Wind_Speed', 'Нет данных'),
                    'Rain_Probability': city.get('Rain_Probability', 'Нет данных'),
                    'Description': city.get('Description', 'Нет данных'),
                    'Weather_Advice': analyze_weather(
                        city.get('Temperature'),
                        city.get('Wind_Speed', 0),
                        city.get('Rain_Probability', 0)
                    )
                })

    return render_template('simple_template.html', results=results, error=error_message)


if __name__ == "__main__":
    app.run(debug=True)