import os
import json
from flask import Flask, render_template_string

# Define Flask app
app = Flask(__name__)

# Retrieve the Cesium Ion Access Token from environment variables
CESIUM_ION_ACCESS_TOKEN = os.environ.get('CESIUM_ION_ACCESS_TOKEN')

# Ensure the Cesium Ion Access Token is available
if not CESIUM_ION_ACCESS_TOKEN:
    raise ValueError("CESIUM_ION_ACCESS_TOKEN environment variable is not set.")

# Read earth-impact-craters.geojson
IMPACT_CRATERS_FILE = 'earth-impact-craters.geojson'
impact_craters = {"type": "FeatureCollection", "features": []}
if os.path.exists(IMPACT_CRATERS_FILE):
    with open(IMPACT_CRATERS_FILE, 'r', encoding='utf-8') as geojson_file:
        impact_craters = json.load(geojson_file)
else:
    print(f"{IMPACT_CRATERS_FILE} not found. Impact craters will not be displayed.")

# HTML template with Cesium-based meteorite impacts and impact craters visualization
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌠 Global Meteorite Impacts and Earth Craters Visualization</title>
    <!-- Include CesiumJS -->
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        /* Existing styles... */

        /* New styles for impact craters filters */
        #craterFilters {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
            align-items: center;
            margin-top: 10px;
        }
        #craterFilters label {
            font-size: 14px;
            color: #333;
        }
        #craterFilters input, #craterFilters select {
            padding: 6px 12px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: #fff;
        }
        /* Update legend icons to be circular */
        .legend-size {
            border-radius: 50%;
            background-color: red;
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>

    <!-- Header with title, description, controls, toggles, and total count -->
    <div id="header">
        <!-- Existing header content... -->

        <!-- Total counts -->
        <div id="totals">
            <div id="totalMeteorites">Total Meteorites: 0</div>
            <div id="totalCraters">Total Impact Craters: 0</div>
        </div>

        <!-- Impact Crater Filters -->
        <div id="craterFilters">
            <div id="diameterRangeContainer">
                <label for="diameterRange">Diameter Range (km): <span id="diameterRangeValue">0 - 300</span></label>
                <input type="range" id="diameterRangeMin" min="0" max="300" value="0" step="1">
                <input type="range" id="diameterRangeMax" min="0" max="300" value="300" step="1">
            </div>
            <div id="ageRangeContainer">
                <label for="ageRange">Age Range (million years): <span id="ageRangeValue">0 - 2000</span></label>
                <input type="range" id="ageRangeMin" min="0" max="2000" value="0" step="1">
                <input type="range" id="ageRangeMax" min="0" max="2000" value="2000" step="1">
            </div>
            <div id="targetRockContainer">
                <label for="targetRockSelect">Target Rock:</label>
                <select id="targetRockSelect" multiple>
                    <!-- Options populated dynamically -->
                </select>
            </div>
        </div>
    </div>

    <!-- Existing content... -->

    <script>
        /* Existing script... */

        // Variables for impact crater filters
        let filteredCraters = [];
        let allCraters = impactCraters.features;

        // Populate target rock options
        function populateTargetRockOptions() {
            const targetRockSet = new Set();
            allCraters.forEach(crater => {
                const targetRock = crater.properties.target_rock || 'Unknown';
                targetRockSet.add(targetRock);
            });
            const targetRockSelect = document.getElementById('targetRockSelect');
            targetRockSet.forEach(rock => {
                const option = document.createElement('option');
                option.value = rock;
                option.text = rock;
                targetRockSelect.add(option);
            });
        }

        // Apply filters to impact craters
        function applyCraterFilters() {
            let diameterMin = parseInt(document.getElementById('diameterRangeMin').value);
            let diameterMax = parseInt(document.getElementById('diameterRangeMax').value);
            let ageMin = parseInt(document.getElementById('ageRangeMin').value);
            let ageMax = parseInt(document.getElementById('ageRangeMax').value);
            const selectedRocks = Array.from(document.getElementById('targetRockSelect').selectedOptions).map(option => option.value);

            // Ensure min is not greater than max
            if (diameterMin > diameterMax) {
                [diameterMin, diameterMax] = [diameterMax, diameterMin];
                document.getElementById('diameterRangeMin').value = diameterMin;
                document.getElementById('diameterRangeMax').value = diameterMax;
            }

            if (ageMin > ageMax) {
                [ageMin, ageMax] = [ageMax, ageMin];
                document.getElementById('ageRangeMin').value = ageMin;
                document.getElementById('ageRangeMax').value = ageMax;
            }

            filteredCraters = allCraters.filter(feature => {
                const properties = feature.properties;
                let diameter = parseFloat(properties.diameter_km) || 0;
                let age = parseFloat(properties.age_millions_years_ago) || 0;
                const targetRock = properties.target_rock || 'Unknown';

                const diameterMatch = diameter >= diameterMin && diameter <= diameterMax;
                const ageMatch = age >= ageMin && age <= ageMax;
                const rockMatch = selectedRocks.length ? selectedRocks.includes(targetRock) : true;

                return diameterMatch && ageMatch && rockMatch;
            });

            updateCraterData();
            updateCraterTotalCount();
        }

        // Update total impact craters count
        function updateCraterTotalCount() {
            document.getElementById('totalCraters').innerText = `Total Impact Craters: ${filteredCraters.length}`;
        }

        // Update impact crater data on the map
        function updateCraterData() {
            craterEntities.entities.removeAll();

            filteredCraters.forEach((feature, index) => {
                const properties = feature.properties;
                const geometry = feature.geometry;

                if (geometry && geometry.type === "Point") {
                    const [lon, lat] = geometry.coordinates;
                    const name = properties.crater_name || 'Unknown';
                    let age = properties.age_millions_years_ago || 'Unknown';
                    let diameter = parseFloat(properties.diameter_km) || 1;
                    const country = properties.country || 'Unknown';
                    const target_rock = properties.target_rock || 'Unknown';
                    const url = properties.url || '#';

                    // Handle uncertainties and units in age
                    if (typeof age === 'string') {
                        age = age.replace(/[^\d\.]/g, '');
                        age = parseFloat(age) || 'Unknown';
                    }

                    craterEntities.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: getCraterSize(diameter),
                            color: Cesium.Color.RED.withAlpha(0.8),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: `
                            <b>Name:</b> <a href="${url}" target="_blank">${name}</a><br>
                            <b>Age:</b> ${age} million years ago<br>
                            <b>Diameter:</b> ${diameter} km<br>
                            <b>Country:</b> ${country}<br>
                            <b>Target Rock:</b> ${target_rock}
                        `,
                        isImpactCrater: true,
                        craterIndex: index
                    });
                }
            });
        }

        // Increase the pick radius for tooltips
        viewer.screenSpaceEventHandler.maximumPickDistance = 15;

        // Update display values for crater filters
        function updateCraterSlidersDisplay() {
            const diameterMin = parseInt(document.getElementById('diameterRangeMin').value);
            const diameterMax = parseInt(document.getElementById('diameterRangeMax').value);
            document.getElementById('diameterRangeValue').innerText = `${diameterMin} - ${diameterMax}`;

            const ageMin = parseInt(document.getElementById('ageRangeMin').value);
            const ageMax = parseInt(document.getElementById('ageRangeMax').value);
            document.getElementById('ageRangeValue').innerText = `${ageMin} - ${ageMax}`;
        }

        // Event listeners for crater filters
        document.getElementById('diameterRangeMin').addEventListener('input', () => {
            applyCraterFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('diameterRangeMax').addEventListener('input', () => {
            applyCraterFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('ageRangeMin').addEventListener('input', () => {
            applyCraterFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('ageRangeMax').addEventListener('input', () => {
            applyCraterFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('targetRockSelect').addEventListener('change', () => {
            applyCraterFilters();
        });

        // Initialize crater filters on page load
        function initializeCraterFilters() {
            populateTargetRockOptions();
            updateCraterSlidersDisplay();
            applyCraterFilters();
        }

        // Call initialize functions on page load
        initializeCraterFilters();

        // Existing initialization code...
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        cesium_token=CESIUM_ION_ACCESS_TOKEN,
        impact_craters=impact_craters
    )

if __name__ == '__main__':
    # Use the port provided by the environment or default to 8080
    port = int(os.environ.get('PORT', 8080))
    # Bind to all network interfaces and use the specified port
    app.run(debug=False, host='0.0.0.0', port=port)
