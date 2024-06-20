from flask import Flask, request, jsonify
import requests
import json
import re
from math import radians, cos, sin, asin, sqrt, ceil

app = Flask(__name__)

def fetch_extreme_values_for_station(station_id):
    url = 'https://ashrae-meteo.info/v2.0/request_meteo_parametres.php'
    
    payload = {
        'wmo': station_id,
        'ashrae_version': '2021',
        'si_ip': 'SI'
    }
    
    headers = {
    "Accept": "*/*",
    "Referer": "https://ashrae-meteo.info/v2.0/"
}
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            response_text = response.text
            
            pattern_min = r'"extreme_annual_DB_mean_min":"([\d.]+)"'
            pattern_max = r'"extreme_annual_DB_mean_max":"([\d.]+)"'
            
            match_min = re.search(pattern_min, response_text)
            match_max = re.search(pattern_max, response_text)
            
            min_value = match_min.group(1) if match_min else None
            max_value = match_max.group(1) if match_max else None
            
            return {
                'station_id': station_id,
                'extreme_annual_DB_mean_min': min_value,
                'extreme_annual_DB_mean_max': max_value
            }
        
        else:
            print(f"Failed to retrieve data for station ID {station_id}. Status code: {response.status_code}")
            return None
        
    except Exception as e:
        print(f"An error occurred for station ID {station_id}: {str(e)}")
        return None

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

@app.route('/<lat>/<long>', methods=['GET'])
def get_weather_data(lat, long):
    url = "https://ashrae-meteo.info/v2.0/request_places.php"

    headers = {
    "Accept": "*/*",
    "Referer": "https://ashrae-meteo.info/v2.0/"
}

    payload = {
        "lat": lat,
        "long": long,
        "number": "10",
        "ashrae_version": "2021"
    }

    response = requests.post(url, headers=headers, data=payload)

    try:
        response_json = response.json()
        stations_id = [station["wmo"] for station in response_json["meteo_stations"]]
        input_lat = float(payload["lat"])
        input_lon = float(payload["long"])

        for station in response_json["meteo_stations"]:
            station_lat = float(station["lat"])
            station_lon = float(station["long"])
            station["distance"] = ceil(haversine(input_lat, input_lon, station_lat, station_lon))
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to decode JSON from response"}), 500

    results = []
    for station_id in stations_id:
        result = fetch_extreme_values_for_station(station_id)
        if result:
            results.append(result)

    combined_data = []

    if response_json:
        for station in response_json["meteo_stations"]:
            for result in results:
                if station["wmo"] == result["station_id"]:
                    combined_station_data = {**station, **result}
                    combined_data.append(combined_station_data)

    return jsonify(combined_data)


@app.route('/')
def index():
    return "Home page"

if __name__ == '__main__':
    app.run(debug=True)
