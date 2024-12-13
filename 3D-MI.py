import os
import json
import re
from flask import Flask, render_template

app = Flask(__name__, static_url_path='/static')

CESIUM_ION_ACCESS_TOKEN = os.environ.get('CESIUM_ION_ACCESS_TOKEN')
if not CESIUM_ION_ACCESS_TOKEN:
    raise ValueError("CESIUM_ION_ACCESS_TOKEN environment variable is not set.")

def parse_age_string(age_str):
    if not age_str:
        return None, None
    age_str = age_str.strip()
    patterns = [
        r'^(?P<age>\d+(\.\d+)?)\s*\±\s*(?P<uncertainty>\d+(\.\d+)?)$',
        r'^~?(?P<min>\d+(\.\d+)?)-(?P<max>\d+(\.\d+)?)$',
        r'^<?(?P<max>\d+(\.\d+)?)$',
        r'^>?(?P<min>\d+(\.\d+)?)$',
        r'^\~?(?P<age>\d+(\.\d+)?)$'
    ]
    for pattern in patterns:
        match = re.match(pattern, age_str)
        if match:
            groups = match.groupdict()
            if 'age' in groups and groups['age']:
                age = float(groups['age'])
                uncertainty = float(groups.get('uncertainty', 0))
                return age - uncertainty, age + uncertainty
            elif 'min' in groups and 'max' in groups and groups['min'] and groups['max']:
                return float(groups['min']), float(groups['max'])
            elif 'min' in groups and groups['min']:
                return float(groups['min']), None  # Return None for max age
            elif 'max' in groups and groups['max']:
                return None, float(groups['max'])  # Return None for min age
    # If no pattern matched, return None
    return None, None

IMPACT_CRATERS_FILE = 'earth-impact-craters-v2.geojson'
impact_craters = {"type": "FeatureCollection", "features": []}
if os.path.exists(IMPACT_CRATERS_FILE):
    with open(IMPACT_CRATERS_FILE, 'r', encoding='utf-8') as geojson_file:
        impact_craters = json.load(geojson_file)
        for feature in impact_craters['features']:
            # Clean up the 'Confirmation' field
            confirmation = feature['properties'].get('Confirmation', '')
            if confirmation:
                cleaned_confirmation = re.sub(r'\d+\.\d+\.CO;2" title="See details" target="_blank">', '', confirmation)
                feature['properties']['Confirmation'] = cleaned_confirmation.strip()

            age_str = feature['properties'].get('Age [Myr]', '')
            age_min, age_max = parse_age_string(age_str)
            feature['properties']['age_min'] = age_min if age_min is not None else 0
            feature['properties']['age_max'] = age_max if age_max is not None else 2500
else:
    print(f"{IMPACT_CRATERS_FILE} not found. Impact craters will not be displayed.")

@app.route('/')
def index():
    return render_template(
        'layout.html',
        cesium_token=CESIUM_ION_ACCESS_TOKEN,
        impact_craters=impact_craters
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)