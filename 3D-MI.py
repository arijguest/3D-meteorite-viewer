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

# HTML template with Cesium-based visualization
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌠 Global Meteorite and Impact Crater Visualization</title>
    <!-- Include CesiumJS -->
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        html, body, #cesiumContainer {
            width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        /* Header Styling */
        #header {
            position: absolute;
            top: 0; left: 0; width: 100%;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 20px;
            box-sizing: border-box;
            z-index: 3;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #header h1 {
            margin: 0;
            font-size: 20px;
            color: #333;
            text-align: center;
        }
        /* Controls Styling */
        #controls {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
            align-items: center;
            margin-top: 10px;
        }
        #controls label {
            font-size: 14px;
            color: #333;
        }
        .range-container {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .range-container input[type="range"] {
            width: 200px;
        }
        #viewToggle {
            margin-top: 10px;
        }
        /* Legend Styling */
        #legend {
            margin-top: 10px;
            background: rgba(255,255,255,0.9);
            padding: 10px 15px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }
        .legend-item {
            display: flex;
            align-items: center;
        }
        .legend-symbol {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 50%;
            background-color: red;
        }
        /* Top Bar Styling */
        #topBar {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 0;
            box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
            z-index: 3;
            display: flex;
            overflow-x: auto;
            align-items: center;
        }
        .bar-item {
            flex: 0 0 auto;
            margin: 0 15px;
            font-size: 14px;
            color: #0078D7;
            cursor: pointer;
            transition: color 0.3s;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .bar-item:hover {
            color: #005a9e;
            text-decoration: underline;
        }
        /* Tooltip Styling */
        #tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            padding: 8px 12px;
            border-radius: 4px;
            pointer-events: none;
            font-size: 13px;
            z-index: 5;
            display: none;
            max-width: 300px;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>

    <!-- Header with title and controls -->
    <div id="header">
        <h1 id="viewTitle">🌠 Meteorite Visualization</h1>
        <div id="controls">
            <div class="range-container" id="firstRangeContainer">
                <label id="firstRangeLabel"></label>
                <input type="range" id="firstRangeMin">
                <input type="range" id="firstRangeMax">
            </div>
            <div class="range-container" id="secondRangeContainer">
                <label id="secondRangeLabel"></label>
                <input type="range" id="secondRangeMin">
                <input type="range" id="secondRangeMax">
            </div>
            <div id="viewToggle">
                <label>
                    <input type="radio" name="viewToggle" value="meteorites" checked>
                    Meteorites
                </label>
                <label>
                    <input type="radio" name="viewToggle" value="craters">
                    Impact Craters
                </label>
            </div>
        </div>
        <!-- Legend -->
        <div id="legend">
            <!-- Populated dynamically -->
        </div>
    </div>

    <!-- Top bar for items -->
    <div id="topBar">
        <!-- Populated dynamically -->
    </div>

    <!-- Tooltip -->
    <div id="tooltip"></div>

    <!-- Script Section -->
    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: false,
            navigationHelpButton: false,
            sceneModePicker: false,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            homeButton: true,
            geocoder: false,
            infoBox: false,
            selectionIndicator: false,
            navigationInstructionsInitiallyVisible: false
        });

        let currentView = 'meteorites'; // 'meteorites' or 'craters'

        // Data sources
        let meteoriteEntities = new Cesium.CustomDataSource('meteorites');
        viewer.dataSources.add(meteoriteEntities);

        let craterEntities = new Cesium.CustomDataSource('craters');
        viewer.dataSources.add(craterEntities);

        let allMeteorites = [];
        let filteredMeteorites = [];
        let allCraters = {{ impact_craters | tojson }}.features || [];
        let filteredCraters = [];

        // Initialize the application
        function initialize() {
            setupView();
            fetchMeteoriteData();
            applyFilters();
            setupEventListeners();
        }

        // Setup the view based on currentView
        function setupView() {
            const viewTitle = document.getElementById('viewTitle');
            const firstRangeLabel = document.getElementById('firstRangeLabel');
            const secondRangeLabel = document.getElementById('secondRangeLabel');
            const firstRangeMin = document.getElementById('firstRangeMin');
            const firstRangeMax = document.getElementById('firstRangeMax');
            const secondRangeMin = document.getElementById('secondRangeMin');
            const secondRangeMax = document.getElementById('secondRangeMax');

            const legend = document.getElementById('legend');
            legend.innerHTML = '';

            if (currentView === 'meteorites') {
                viewTitle.innerText = '🌠 Meteorite Visualization';

                firstRangeLabel.innerText = 'Year Range';
                firstRangeMin.min = 860;
                firstRangeMin.max = 2023;
                firstRangeMin.value = 860;
                firstRangeMax.min = 860;
                firstRangeMax.max = 2023;
                firstRangeMax.value = 2023;

                secondRangeLabel.innerText = 'Mass Range (g)';
                secondRangeMin.min = 0;
                secondRangeMin.max = 600000;
                secondRangeMin.value = 0;
                secondRangeMax.min = 0;
                secondRangeMax.max = 600000;
                secondRangeMax.value = 600000;

                // Legend for Meteorites
                const legendItems = [
                    { color: 'cyan', label: 'Mass < 1,000g' },
                    { color: 'green', label: '1,000g ≤ Mass < 10,000g' },
                    { color: 'yellow', label: '10,000g ≤ Mass < 50,000g' },
                    { color: 'orange', label: '50,000g ≤ Mass < 100,000g' },
                    { color: 'red', label: 'Mass ≥ 100,000g' },
                ];
                legendItems.forEach(item => {
                    const legendItem = document.createElement('div');
                    legendItem.className = 'legend-item';
                    legendItem.innerHTML = `
                        <div class="legend-symbol" style="background-color: ${item.color};"></div>
                        <span>${item.label}</span>
                    `;
                    legend.appendChild(legendItem);
                });
            } else if (currentView === 'craters') {
                viewTitle.innerText = '🕳️ Impact Crater Visualization';

                firstRangeLabel.innerText = 'Age Range (Ma)';
                firstRangeMin.min = 0;
                firstRangeMin.max = 2000;
                firstRangeMin.value = 0;
                firstRangeMax.min = 0;
                firstRangeMax.max = 2000;
                firstRangeMax.value = 2000;

                secondRangeLabel.innerText = 'Diameter Range (km)';
                secondRangeMin.min = 0;
                secondRangeMin.max = 300;
                secondRangeMin.value = 0;
                secondRangeMax.min = 0;
                secondRangeMax.max = 300;
                secondRangeMax.value = 300;

                // Legend for Impact Craters
                const legendItems = [
                    { color: 'lightblue', label: 'Diameter < 10km' },
                    { color: 'green', label: '10km ≤ Diameter < 30km' },
                    { color: 'yellow', label: '30km ≤ Diameter < 50km' },
                    { color: 'orange', label: '50km ≤ Diameter < 100km' },
                    { color: 'red', label: 'Diameter ≥ 100km' },
                ];
                legendItems.forEach(item => {
                    const legendItem = document.createElement('div');
                    legendItem.className = 'legend-item';
                    legendItem.innerHTML = `
                        <div class="legend-symbol" style="background-color: ${item.color};"></div>
                        <span>${item.label}</span>
                    `;
                    legend.appendChild(legendItem);
                });
            }
        }

        // Fetch meteorite data
        function fetchMeteoriteData() {
            const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=10000';
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (!data) throw new Error('Invalid meteorite data format.');
                    allMeteorites = data;
                    applyFilters();
                })
                .catch(error => {
                    console.error('Error fetching meteorite data:', error);
                });
        }

        // Apply filters based on the current view
        function applyFilters() {
            if (currentView === 'meteorites') {
                filterMeteorites();
                updateMeteoriteData();
                updateTopBar();
            } else if (currentView === 'craters') {
                filterCraters();
                updateCraterData();
                updateTopBar();
            }
        }

        // Filter meteorites
        function filterMeteorites() {
            const yearMin = parseInt(document.getElementById('firstRangeMin').value);
            const yearMax = parseInt(document.getElementById('firstRangeMax').value);
            const massMin = parseInt(document.getElementById('secondRangeMin').value);
            const massMax = parseInt(document.getElementById('secondRangeMax').value);

            filteredMeteorites = allMeteorites.filter(m => {
                const year = m.year ? new Date(m.year).getFullYear() : null;
                const mass = m.mass ? parseFloat(m.mass) : null;

                const yearMatch = year ? (year >= yearMin && year <= yearMax) : true;
                const massMatch = mass ? (mass >= massMin && mass <= massMax) : true;

                return yearMatch && massMatch;
            });
        }

        // Filter craters
        function filterCraters() {
            const ageMin = parseFloat(document.getElementById('firstRangeMin').value);
            const ageMax = parseFloat(document.getElementById('firstRangeMax').value);
            const diameterMin = parseFloat(document.getElementById('secondRangeMin').value);
            const diameterMax = parseFloat(document.getElementById('secondRangeMax').value);

            filteredCraters = allCraters.filter(c => {
                const ageStr = c.properties.age_millions_years_ago || '';
                const age = parseFloat(ageStr.replace(/[^\d\.]/g, '')) || null;
                const diameter = c.properties.diameter_km ? parseFloat(c.properties.diameter_km) : null;

                const ageMatch = age ? (age >= ageMin && age <= ageMax) : true;
                const diameterMatch = diameter ? (diameter >= diameterMin && diameter <= diameterMax) : true;

                return ageMatch && diameterMatch;
            });
        }

        // Update meteorite data on the map
        function updateMeteoriteData() {
            meteoriteEntities.entities.removeAll();

            filteredMeteorites.forEach((meteorite, index) => {
                let lat, lon;

                if (meteorite.geolocation) {
                    if (meteorite.geolocation.latitude && meteorite.geolocation.longitude) {
                        lat = parseFloat(meteorite.geolocation.latitude);
                        lon = parseFloat(meteorite.geolocation.longitude);
                    } else if (meteorite.geolocation.coordinates && meteorite.geolocation.coordinates.length === 2) {
                        lon = parseFloat(meteorite.geolocation.coordinates[0]);
                        lat = parseFloat(meteorite.geolocation.coordinates[1]);
                    }
                } else if (meteorite.reclat && meteorite.reclong) {
                    lat = parseFloat(meteorite.reclat);
                    lon = parseFloat(meteorite.reclong);
                }

                if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
                    const name = meteorite.name || 'Unknown';
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                    const massDisplay = formatMass(mass);
                    const recclass = meteorite.recclass || 'Unknown';
                    const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                    const fall = meteorite.fall || 'Unknown';

                    meteoriteEntities.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 5000, 5), 20) : 5,
                            color: getMeteoriteColor(mass),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: `
                            <b>Name:</b> ${name}<br>
                            <b>Mass:</b> ${massDisplay}<br>
                            <b>Class:</b> ${recclass}<br>
                            <b>Year:</b> ${year}<br>
                            <b>Fall/Find:</b> ${fall}
                        `,
                        meteoriteIndex: index
                    });
                }
            });
        }

        // Update impact crater data on the map
        function updateCraterData() {
            craterEntities.entities.removeAll();

            filteredCraters.forEach((crater, index) => {
                const geometry = crater.geometry;
                const properties = crater.properties;

                if (geometry && geometry.type === 'Point') {
                    const [lon, lat] = geometry.coordinates;
                    const name = properties.crater_name || 'Unknown';
                    const diameter = properties.diameter_km ? parseFloat(properties.diameter_km) : 'Unknown';
                    const diameterDisplay = diameter + ' km';
                    const age = properties.age_millions_years_ago || 'Unknown';
                    const url = properties.url || '#';

                    craterEntities.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: diameter !== 'Unknown' ? Math.min(Math.max(diameter / 5, 5), 20) : 5,
                            color: getCraterColor(diameter),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: `
                            <b>Name:</b> <a href="${url}" target="_blank">${name}</a><br>
                            <b>Diameter:</b> ${diameterDisplay}<br>
                            <b>Age:</b> ${age} million years ago<br>
                            <b>More Info:</b> <a href="${url}" target="_blank">Click here</a>
                        `,
                        craterIndex: index
                    });
                }
            });
        }

        // Get color based on mass
        function getMeteoriteColor(mass) {
            if (mass === 'Unknown' || isNaN(mass)) return Cesium.Color.GRAY;
            if (mass >= 100000) return Cesium.Color.RED;
            if (mass >= 50000) return Cesium.Color.ORANGE;
            if (mass >= 10000) return Cesium.Color.YELLOW;
            if (mass >= 1000) return Cesium.Color.GREEN;
            return Cesium.Color.CYAN;
        }

        // Get color based on diameter
        function getCraterColor(diameter) {
            if (diameter === 'Unknown' || isNaN(diameter)) return Cesium.Color.GRAY;
            if (diameter >= 100) return Cesium.Color.RED;
            if (diameter >= 50) return Cesium.Color.ORANGE;
            if (diameter >= 30) return Cesium.Color.YELLOW;
            if (diameter >= 10) return Cesium.Color.GREEN;
            return Cesium.Color.LIGHTBLUE;
        }

        // Format mass or diameter
        function formatMass(value) {
            if (value === 'Unknown' || isNaN(value)) return 'Unknown';
            if (currentView === 'meteorites') {
                if (value >= 1000) return (value / 1000).toFixed(2) + ' kg';
                return value + ' g';
            } else {
                return value + ' km';
            }
        }

        // Update top bar
        function updateTopBar() {
            const topBar = document.getElementById('topBar');
            topBar.innerHTML = '';

            const titleItem = document.createElement('div');
            titleItem.className = 'bar-item';
            if (currentView === 'meteorites') {
                titleItem.innerHTML = '<strong>Top Meteorites:</strong>';
                topBar.appendChild(titleItem);

                const sortedMeteorites = filteredMeteorites.sort((a, b) => parseFloat(b.mass || 0) - parseFloat(a.mass || 0));
                const topItems = sortedMeteorites.slice(0, 10);

                topItems.forEach((meteorite, index) => {
                    const name = meteorite.name || 'Unknown';
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                    const massDisplay = formatMass(mass);
                    const barItem = document.createElement('div');
                    barItem.className = 'bar-item';
                    barItem.innerText = `${name} - ${massDisplay}`;
                    barItem.onclick = () => flyToMeteorite(index);
                    topBar.appendChild(barItem);
                });
            } else {
                titleItem.innerHTML = '<strong>Top Impact Craters:</strong>';
                topBar.appendChild(titleItem);

                const sortedCraters = filteredCraters.sort((a, b) => parseFloat(b.properties.diameter_km || 0) - parseFloat(a.properties.diameter_km || 0));
                const topItems = sortedCraters.slice(0, 10);

                topItems.forEach((crater, index) => {
                    const name = crater.properties.crater_name || 'Unknown';
                    const diameter = crater.properties.diameter_km ? parseFloat(crater.properties.diameter_km) : 'Unknown';
                    const diameterDisplay = formatMass(diameter);
                    const barItem = document.createElement('div');
                    barItem.className = 'bar-item';
                    barItem.innerText = `${name} - ${diameterDisplay}`;
                    barItem.onclick = () => flyToCrater(index);
                    topBar.appendChild(barItem);
                });
            }
        }

        // Fly to meteorite
        function flyToMeteorite(index) {
            const meteorite = filteredMeteorites[index];
            if (!meteorite) return;

            let lat, lon;

            if (meteorite.geolocation) {
                if (meteorite.geolocation.latitude && meteorite.geolocation.longitude) {
                    lat = parseFloat(meteorite.geolocation.latitude);
                    lon = parseFloat(meteorite.geolocation.longitude);
                } else if (meteorite.geolocation.coordinates && meteorite.geolocation.coordinates.length === 2) {
                    lon = parseFloat(meteorite.geolocation.coordinates[0]);
                    lat = parseFloat(meteorite.geolocation.coordinates[1]);
                }
            } else if (meteorite.reclat && meteorite.reclong) {
                lat = parseFloat(meteorite.reclat);
                lon = parseFloat(meteorite.reclong);
            }

            if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
                viewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(lon, lat, 1500000),
                    duration: 2
                });
            }
        }

        // Fly to crater
        function flyToCrater(index) {
            const crater = filteredCraters[index];
            if (!crater) return;

            const geometry = crater.geometry;

            if (geometry && geometry.type === 'Point') {
                const [lon, lat] = geometry.coordinates;

                if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
                    viewer.camera.flyTo({
                        destination: Cesium.Cartesian3.fromDegrees(lon, lat, 1500000),
                        duration: 2
                    });
                }
            }
        }

        // Tooltip functionality
        const tooltip = document.getElementById('tooltip');
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

        handler.setInputAction(movement => {
            const picked = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(picked) && picked.id) {
                tooltip.style.display = 'block';
                tooltip.innerHTML = picked.id.description.getValue();
                tooltip.style.left = movement.endPosition.x + 15 + 'px';
                tooltip.style.top = movement.endPosition.y + 15 + 'px';
            } else {
                tooltip.style.display = 'none';
            }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

        // Setup event listeners
        function setupEventListeners() {
            // View toggle
            const viewToggleRadioButtons = document.querySelectorAll('input[name="viewToggle"]');
            viewToggleRadioButtons.forEach(radio => {
                radio.addEventListener('change', event => {
                    currentView = event.target.value;
                    setupView();
                    applyFilters();
                    meteoriteEntities.show = currentView === 'meteorites';
                    craterEntities.show = currentView === 'craters';
                });
            });

            // Sliders
            const sliders = document.querySelectorAll('input[type="range"]');
            sliders.forEach(slider => {
                slider.addEventListener('input', () => {
                    applyFilters();
                });
            });
        }

        // Initialize the application
        initialize();
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
