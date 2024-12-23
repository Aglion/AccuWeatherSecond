import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from weather_api import get_location_key, get_weather_forecast
from data_processing import process_weather_data
import os
from dotenv import load_dotenv
import dash_bootstrap_components as dbc

load_dotenv()
API_KEY = os.getenv('ACCUWEATHER_API_KEY')

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
app.title = 'Прогноз погоды для маршрута'

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        .dash-debug-menu {
            display: none !important;
        }
        </style>
    </head>
    <body>
        {%config%}
        {%scripts%}
        {%renderer%}
        <div id="react-entry-point">
            {%app_entry%}
        </div>
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

cities = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Нижний Новгород']

city_coordinates = {
    'Москва': {'lat': 55.7558, 'lon': 37.6173},
    'Санкт-Петербург': {'lat': 59.9343, 'lon': 30.3351},
    'Новосибирск': {'lat': 55.0084, 'lon': 82.9357},
    'Екатеринбург': {'lat': 56.8389, 'lon': 60.6057},
    'Нижний Новгород': {'lat': 56.2965, 'lon': 43.9361}
}

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Прогноз погоды для маршрута"), width=12, className="text-center my-4")
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Выберите начальную точку:'),
            dcc.Dropdown(
                id='start-point-dropdown',
                options=[{'label': city, 'value': city} for city in cities],
                value=cities[0],
                clearable=False
            )
        ], width=4),
        dbc.Col([
            html.Label('Выберите конечную точку:'),
            dcc.Dropdown(
                id='end-point-dropdown',
                options=[{'label': city, 'value': city} for city in cities],
                value=cities[-1],
                clearable=False
            )
        ], width=4),
        dbc.Col([
            html.Label('Выберите промежуточные точки (если есть):'),
            dcc.Dropdown(
                id='intermediate-points-dropdown',
                options=[{'label': city, 'value': city} for city in cities],
                multi=True,
                placeholder='Выберите промежуточные точки'
            )
        ], width=4),
    ]),
    dbc.Row([
        dbc.Col([
            html.Label('Выберите количество дней для прогноза:'),
            dcc.Dropdown(
                id='days-dropdown',
                options=[
                    {'label': '1 день', 'value': 1},
                    {'label': '3 дня', 'value': 3},
                    {'label': '5 дней', 'value': 5}
                ],
                value=5,
                clearable=False
            )
        ], width=6),
        dbc.Col([
            html.Label('Выберите параметры для отображения:'),
            dcc.Checklist(
                id='parameter-checklist',
                options=[
                    {'label': 'Температура (°C)', 'value': 'temperature'},
                    {'label': 'Скорость ветра (м/с)', 'value': 'wind_speed'},
                    {'label': 'Осадки (%)', 'value': 'precipitation'}
                ],
                value=['temperature', 'wind_speed', 'precipitation'],
                labelStyle={'display': 'inline-block', 'margin-right': '10px'}
            )
        ], width=6),
    ], style={'marginTop': '20px'}),
    dbc.Row([
        dbc.Col([
            dbc.Button('Обновить прогноз', id='update-button', n_clicks=0, color='primary', style={'width': '100%'})
        ], width=12, style={'marginTop': '20px'}),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='weather-graph')
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='map-graph')
        ], width=12)
    ]),
    dbc.Toast(
        "Прогноз успешно обновлен!",
        id="success-toast",
        header="Успех",
        is_open=False,
        dismissable=True,
        duration=5000,
        style={"position": "fixed", "top": 10, "right": 10, "width": 350},
    ),
    dbc.Toast(
        "Ошибка при получении данных о погоде.",
        id="error-toast",
        header="Ошибка",
        is_open=False,
        dismissable=True,
        duration=5000,
        style={"position": "fixed", "top": 10, "right": 10, "width": 350},
        color="danger",
    ),
], fluid=True)

@app.callback(
    [
        Output('weather-graph', 'figure'),
        Output('map-graph', 'figure'),
        Output("success-toast", "is_open"),
        Output("error-toast", "is_open"),
    ],
    Input('update-button', 'n_clicks'),
    State('start-point-dropdown', 'value'),
    State('end-point-dropdown', 'value'),
    State('intermediate-points-dropdown', 'value'),
    State('days-dropdown', 'value'),
    State('parameter-checklist', 'value')
)
def update_weather(n_clicks, start, end, intermediates, days, parameters):
    if n_clicks == 0:
        return {}, {}, False, False

    points = [start]
    if intermediates:
        points.extend(intermediates)
    points.append(end)

    location_keys = {}
    for city in points:
        key = get_location_key(city)
        if key:
            location_keys[city] = key

    weather_data = {}
    success = True
    for city, key in location_keys.items():
        forecast = get_weather_forecast(key, days=days)
        if forecast:
            weather_data[city] = forecast
        else:
            success = False

    if not weather_data:
        return {}, {}, False, True

    processed_weather = process_weather_data(weather_data)

    traces = []
    for city, data in processed_weather.items():
        dates = data.get('dates', [])
        if 'temperature' in parameters:
            traces.append(go.Scatter(
                x=dates,
                y=data.get('temperatures', []),
                mode='lines+markers',
                name=f'{city} Температура (°C)',
                hoverinfo='x+y+name',
                line=dict(width=2)
            ))
        if 'wind_speed' in parameters:
            traces.append(go.Bar(
                x=dates,
                y=data.get('wind_speeds', []),
                name=f'{city} Скорость ветра (м/с)',
                opacity=0.6
            ))
        if 'precipitation' in parameters:
            traces.append(go.Scatter(
                x=dates,
                y=data.get('precipitation_probs', []),
                mode='lines+markers',
                name=f'{city} Осадки (%)',
                hoverinfo='x+y+name',
                yaxis='y2',
                line=dict(dash='dot', width=2)
            ))

    layout = go.Layout(
        title='Прогноз погоды по маршруту',
        xaxis=dict(title='Дата'),
        yaxis=dict(title='Температура (°C) / Скорость ветра (м/с)'),
        yaxis2=dict(title='Осадки (%)', overlaying='y', side='right'),
        legend=dict(x=0, y=1.2, orientation='h'),
        hovermode='closest',
        margin=dict(l=60, r=60, t=80, b=60),
        template='plotly_white'
    )

    weather_fig = go.Figure(data=traces, layout=layout)

    lats = [city_coordinates[city]['lat'] for city in points]
    lons = [city_coordinates[city]['lon'] for city in points]

    route_trace = go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='lines',
        line=dict(width=2, color='blue'),
        hoverinfo='none',
        name='Маршрут'
    )

    marker_traces = []
    for city in points:
        if city in processed_weather:
            latest_weather = processed_weather[city]
            temp = latest_weather['temperatures'][0] if latest_weather['temperatures'] else 'N/A'
            wind = latest_weather['wind_speeds'][0] if latest_weather['wind_speeds'] else 'N/A'
            precip = latest_weather['precipitation_probs'][0] if latest_weather['precipitation_probs'] else 'N/A'
            hover_text = f"{city}<br>Температура: {temp}°C<br>Ветер: {wind} м/с<br>Осадки: {precip}%"

            marker_traces.append(go.Scattermapbox(
                lat=[city_coordinates[city]['lat']],
                lon=[city_coordinates[city]['lon']],
                mode='markers',
                marker=dict(size=10, color='red'),
                name=city,
                hoverinfo='text',
                text=hover_text
            ))

    map_traces = [route_trace] + marker_traces

    map_layout = go.Layout(
        title='Маршрут с прогнозами погоды',
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            bearing=0,
            center=dict(lat=56.0, lon=50.0),
            pitch=0,
            zoom=3,
            style='open-street-map'
        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )

    map_fig = go.Figure(data=map_traces, layout=map_layout)

    if success:
        return weather_fig, map_fig, True, False
    else:
        return weather_fig, map_fig, False, True

if __name__ == '__main__':
    app.run_server(debug=False)