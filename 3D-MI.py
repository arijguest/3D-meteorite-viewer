import os
import json
import re
from flask import Flask, render_template_string

app = Flask(__name__)

CESIUM_ION_ACCESS_TOKEN = os.environ.get('CESIUM_ION_ACCESS_TOKEN')
if not CESIUM_ION_ACCESS_TOKEN:
    raise ValueError("CESIUM_ION_ACCESS_TOKEN environment variable is not set.")

def parse_age_string(age_str):
    if not age_str:
        return None, None
    age_str = age_str.strip()
    patterns = [
        r'^(?P<age>\d+)\s*\±\s*(?P<uncertainty>\d+)$',
        r'^~?(?P<min>\d+)-(?P<max>\d+)$',
        r'^<?(?P<max>\d+)$',
        r'^>?(?P<min>\d+(\.\d+)?)$',
        r'^(?P<age>\d+(\.\d+)?)$'
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
                return float(groups['min']), 2000
            elif 'max' in groups and groups['max']:
                return 0, float(groups['max'])
    return None, None

IMPACT_CRATERS_FILE = 'earth-impact-craters.geojson'
impact_craters = {"type": "FeatureCollection", "features": []}
if os.path.exists(IMPACT_CRATERS_FILE):
    with open(IMPACT_CRATERS_FILE, 'r', encoding='utf-8') as geojson_file:
        impact_craters = json.load(geojson_file)
        for feature in impact_craters['features']:
            age_str = feature['properties'].get('age_millions_years_ago', '')
            age_min, age_max = parse_age_string(age_str)
            feature['properties']['age_min'] = age_min if age_min is not None else 0
            feature['properties']['age_max'] = age_max if age_max is not None else 2000
else:
    print(f"{IMPACT_CRATERS_FILE} not found. Impact craters will not be displayed.")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌠 Global Meteorite Impacts and Earth Craters Visualization</title>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        html, body, #cesiumContainer {
            width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #header {
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            padding: 10px;
            z-index: 1;
            color: white;
            text-align: center;
            border-radius: 5px;
        }
        #header h1 {
            margin: 0;
            font-size: 24px;
        }
        #header div {
            margin-top: 10px;
        }
        #controls {
            position: absolute;
            top: 70px;
            left: 10px;
            background: rgba(0, 0, 0, 0.9);
            padding: 30px 10px 10px 10px; /* Increased top padding */
            z-index: 1;
            color: white;
            border-radius: 5px;
            max-height: calc(100% - 80px);
            overflow-y: auto;
            display: none;
            width: 300px;
        }
        #controls .close-button {
            position: absolute;
            top: 10px;
            right: 10px;
            background: transparent;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
        }
        #meteoriteBar, #craterBar {
            position: absolute;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            overflow-x: auto;
            padding: 5px 0;
            z-index: 1;
        }
        #meteoriteBar {
            bottom: 0;
        }
        #craterBar {
            bottom: 50px; /* Positioned above meteoriteBar */
        }
        .bar-item {
            color: white;
            flex: 0 0 auto;
            padding: 5px 10px;
            cursor: pointer;
            white-space: nowrap;
        }
        .bar-item:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        #tooltip {
            position: absolute;
            pointer-events: none;
            z-index: 999;
            background-color: rgba(0,0,0,0.7);
            color: white;
            padding: 10px;
            border-radius: 5px;
            max-width: 300px;
        }
        #tooltip a {
            color: lightblue;
            text-decoration: underline;
        }
        #modal, #craterModal, #infoModal {
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.7);
        }
        #modal-content, #craterModal-content, #infoModal-content {
            background-color: #2b2b2b;
            margin: 5% auto;
            padding: 20px;
            width: 80%;
            color: white;
            border-radius: 5px;
            position: relative;
        }
        #closeModal, #closeCraterModal, #closeInfoModal, #controls .close-button {
            color: #aaa;
            position: absolute;
            top: 10px;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        #closeModal:hover, #closeModal:focus, #closeCraterModal:hover, #closeCraterModal:focus,
        #closeInfoModal:hover, #closeInfoModal:focus, #controls .close-button:hover, #controls .close-button:focus {
            color: white;
            text-decoration: none;
        }
        #fullMeteoriteTable, #fullCraterTable {
            width: 100%;
            border-collapse: collapse;
        }
        #fullMeteoriteTable th, #fullMeteoriteTable td,
        #fullCraterTable th, #fullCraterTable td {
            border: 1px solid #444;
            padding: 8px;
            text-align: left;
        }
        #fullMeteoriteTable th, #fullCraterTable th {
            background-color: #555;
        }
        input[type="range"] {
            width: 100%;
        }
        select {
            width: 100%;
        }
        #searchContainer {
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }
        #searchInput {
            flex: 1;
        }
        button, input[type="button"] {
            cursor: pointer;
        }
        label {
            display: block;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="header">
        <h1>🌠 Global Meteorite Impacts and Earth Craters Visualization</h1>
        <div>
            <button id="optionsButton">⚙️ Options</button>
        </div>
    </div>
    <div id="controls">
        <button class="close-button" id="closeOptions">&times;</button>
        <div id="searchContainer">
            <input type="text" id="searchInput" placeholder="Search location...">
            <button id="searchButton">Search</button>
        </div>
        <div>
            <label for="basemapSelector"><strong>Basemap:</strong></label>
            <select id="basemapSelector">
                <option value="Cesium World Imagery">Cesium World Imagery</option>
                <option value="OpenStreetMap">OpenStreetMap</option>
            </select>
        </div>
        <hr>
        <div>
            <label><input type="checkbox" id="toggleMeteorites" checked> Show Meteorites</label>
        </div>
        <div>
            <label><strong>Year Range:</strong> <span id="yearRangeValue"></span></label>
            <input type="range" id="yearRangeMin" min="860" max="2023" value="860">
            <input type="range" id="yearRangeMax" min="860" max="2023" value="2023">
        </div>
        <div>
            <label><strong>Mass Range:</strong> <span id="massRangeValue"></span></label>
            <input type="range" id="massRangeMin" min="0" max="60000" value="0">
            <input type="range" id="massRangeMax" min="0" max="60000" value="60000">
        </div>
        <hr>
        <div>
            <label><input type="checkbox" id="toggleCraters" checked> Show Impact Craters</label>
        </div>
        <div>
            <label><strong>Diameter Range (km):</strong> <span id="diameterRangeValue"></span></label>
            <input type="range" id="diameterRangeMin" min="0" max="300" value="0">
            <input type="range" id="diameterRangeMax" min="0" max="300" value="300">
        </div>
        <div>
            <label><strong>Age Range:</strong> <span id="ageRangeValue"></span></label>
            <input type="range" id="ageRangeMin" min="0" max="2000" value="0">
            <input type="range" id="ageRangeMax" min="0" max="2000" value="2000">
        </div>
        <div>
            <label><strong>Target Rock:</strong></label>
            <select id="targetRockSelect" multiple size="5"></select>
        </div>
        <hr>
        <div>
            <button id="refreshButton">Reset Filters</button>
        </div>
        <hr>
        <div>
            <span id="totalMeteorites">Total Meteorites: 0</span><br>
            <span id="totalCraters">Total Impact Craters: 0</span>
        </div>
        <div>
            <button id="infoButton">ℹ️ Info</button>
        </div>
    </div>
    <div id="craterBar"></div>
    <div id="meteoriteBar"></div>
    <div id="tooltip"></div>
    
    <!-- Meteorite Modal -->
    <div id="modal">
        <div id="modal-content">
            <span id="closeModal">&times;</span>
            <h2>All Meteorites</h2>
            <table id="fullMeteoriteTable">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Mass</th>
                        <th>Class</th>
                        <th>Year</th>
                        <th>Fall/Find</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
    
    <!-- Crater Modal -->
    <div id="craterModal">
        <div id="craterModal-content">
            <span id="closeCraterModal">&times;</span>
            <h2>All Craters</h2>
            <table id="fullCraterTable">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Diameter (km)</th>
                        <th>Age (Ma)</th>
                        <th>Country</th>
                        <th>Target Rock</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
    
    <!-- Info Modal -->
    <div id="infoModal">
        <div id="infoModal-content">
            <span id="closeInfoModal">&times;</span>
            <h2>Information</h2>
            <p>Welcome to the Global Meteorite Impacts and Earth Craters Visualization App. This interactive tool allows you to explore meteorite landings recorded by NASA and discover impact craters around the world.</p>
            <h3>How to Use:</h3>
            <ul>
                <li><strong>Navigation:</strong> Use your mouse or touch controls to navigate around the globe.</li>
                <li><strong>Search:</strong> Use the search bar to fly to a specific location.</li>
                <li><strong>Filters:</strong> Adjust the sliders and dropdowns in the controls menu to filter meteorites and craters based on various criteria such as year, mass, diameter, age, and target rock type.</li>
                <li><strong>Show/Hide Data:</strong> Toggle the visibility of meteorites and craters using the checkboxes.</li>
                <li><strong>Reset Filters:</strong> Click the "Reset Filters" button to return all filters to their default settings.</li>
                <li><strong>Top Meteorites:</strong> View the top meteorites by mass at the bottom bar and click on them to fly to their location.</li>
                <li><strong>Top Craters:</strong> View the top impact craters by diameter just above the meteorites bar and click on them to fly to their location.</li>
                <li><strong>Details:</strong> Click on any meteorite or crater marker to view detailed information.</li>
                <li><strong>View All Meteorites:</strong> Click on "View All" in the top meteorites bar to see a full list of meteorites and navigate to them.</li>
            </ul>
            <h3>Data Sources:</h3>
            <ul>
                <li><a href="https://data.nasa.gov/Space-Science/Meteorite-Landings/gh4g-9sfh" target="_blank">NASA Meteorite Landings Dataset</a></li>
                <li><a href="https://github.com/Antash/earth-impact-db" target="_blank">Earth Impact Database</a></li>
            </ul>
            <p>This application utilizes CesiumJS for 3D globe visualization.</p>
        </div>
    </div>
    
    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: false,
            navigationHelpButton: true,
            sceneModePicker: true,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            homeButton: true,
            geocoder: false,
            infoBox: false,
            selectionIndicator: false,
            navigationInstructionsInitiallyVisible: false
        });

        let allMeteorites = [];
        let filteredMeteorites = [];
        const impactCraters = {{ impact_craters | tojson }};
        let filteredCraters = [];
        const allCraters = impact_craters.features;

        let meteoriteEntities = new Cesium.CustomDataSource('meteorites');
        viewer.dataSources.add(meteoriteEntities);

        let craterEntities = new Cesium.CustomDataSource('craters');
        viewer.dataSources.add(craterEntities);

        function getMeteoriteColor(mass) {
            if (mass >= 100000) return Cesium.Color.RED.withAlpha(0.6);
            if (mass >= 50000)  return Cesium.Color.ORANGE.withAlpha(0.6);
            if (mass >= 10000)  return Cesium.Color.YELLOW.withAlpha(0.6);
            if (mass >= 1000)   return Cesium.Color.GREEN.withAlpha(0.6);
            return Cesium.Color.CYAN.withAlpha(0.6);
        }

        function getCraterColor(diameter) {
            if (diameter >= 50) return Cesium.Color.NAVY.withAlpha(0.8);
            if (diameter >= 30) return Cesium.Color.DARKBLUE.withAlpha(0.8);
            if (diameter >= 10) return Cesium.Color.BLUE.withAlpha(0.8);
            return Cesium.Color.LIGHTBLUE.withAlpha(0.8);
        }

        function fetchAllMeteorites() {
            const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=10000';
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    allMeteorites = data;
                    applyFilters();
                })
                .catch(error => {
                    console.error('Error fetching meteorite data:', error);
                });
        }

        function applyFilters() {
            let yearMin = parseInt(document.getElementById('yearRangeMin').value);
            let yearMax = parseInt(document.getElementById('yearRangeMax').value);
            let massMin = parseInt(document.getElementById('massRangeMin').value);
            let massMax = parseInt(document.getElementById('massRangeMax').value);

            let diameterMin = parseInt(document.getElementById('diameterRangeMin').value);
            let diameterMax = parseInt(document.getElementById('diameterRangeMax').value);
            let ageMin = parseInt(document.getElementById('ageRangeMin').value);
            let ageMax = parseInt(document.getElementById('ageRangeMax').value);
            const selectedRocks = Array.from(document.getElementById('targetRockSelect').selectedOptions).map(option => option.value);

            if (yearMin > yearMax) {
                [yearMin, yearMax] = [yearMax, yearMin];
                document.getElementById('yearRangeMin').value = yearMin;
                document.getElementById('yearRangeMax').value = yearMax;
            }

            if (massMin > massMax) {
                [massMin, massMax] = [massMax, massMin];
                document.getElementById('massRangeMin').value = massMin;
                document.getElementById('massRangeMax').value = massMax;
            }

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

            filteredMeteorites = allMeteorites.filter(m => {
                const year = m.year ? new Date(m.year).getFullYear() : null;
                const mass = m.mass ? parseFloat(m.mass) : null;

                const yearMatch = year ? (year >= yearMin && year <= yearMax) : true;
                const massMatch = mass ? (mass >= massMin && mass <= massMax) : true;

                return yearMatch && massMatch;
            });

            filteredCraters = allCraters.filter(feature => {
                const properties = feature.properties;
                let diameter = parseFloat(properties.diameter_km) || 0;
                let age_min = parseFloat(properties.age_min) || 0;
                let age_max = parseFloat(properties.age_max) || 2000;
                const targetRock = properties.target_rock || 'Unknown';

                const diameterMatch = diameter >= diameterMin && diameter <= diameterMax;
                const ageMatch = (age_min >= ageMin && age_max <= ageMax);
                const rockMatch = selectedRocks.length ? selectedRocks.includes(targetRock) : true;

                return diameterMatch && ageMatch && rockMatch;
            });

            updateMeteoriteData();
            updateCraterData();
            updateTopMeteorites();
            updateTopCraters(); // Added function call
            updateTotalCounts();
            updateModalTable();
            updateCraterModalTable(); // Ensure crater modal table is updated
        }

        function updateTotalCounts() {
            document.getElementById('totalMeteorites').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
            document.getElementById('totalCraters').innerText = `Total Impact Craters: ${filteredCraters.length}`;
        }

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
                    const id = meteorite.id || 'Unknown';
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                    const massDisplay = formatMass(mass);
                    const recclass = meteorite.recclass || 'Unknown';
                    const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                    const fall = meteorite.fall || 'Unknown';

                    meteoriteEntities.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 1000, 5), 15) : 5,
                            color: mass !== 'Unknown' ? getMeteoriteColor(mass) : Cesium.Color.GRAY.withAlpha(0.6),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: `
                            <b>Name:</b> ${name}<br>
                            <b>ID:</b> ${id}<br>
                            <b>Latitude:</b> ${lat.toFixed(5)}<br>
                            <b>Longitude:</b> ${lon.toFixed(5)}<br>
                            <b>Mass:</b> ${massDisplay}<br>
                            <b>Class:</b> ${recclass}<br>
                            <b>Year:</b> ${year}<br>
                            <b>Fall/Find:</b> ${fall}
                        `,
                        isMeteorite: true,
                        meteoriteIndex: index
                    });
                }
            });
        }

        function updateCraterData() {
            craterEntities.entities.removeAll();

            filteredCraters.forEach((feature, index) => {
                const properties = feature.properties;
                const geometry = feature.geometry;

                if (geometry && geometry.type === "Point") {
                    const [lon, lat] = geometry.coordinates;
                    const name = properties.crater_name || 'Unknown';
                    const age = properties.age_millions_years_ago || 'Unknown';
                    let diameter = parseFloat(properties.diameter_km) || 1;
                    const country = properties.country || 'Unknown';
                    const target_rock = properties.target_rock || 'Unknown';
                    const url = properties.url || '#';

                    craterEntities.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: getCraterSize(diameter),
                            color: getCraterColor(diameter),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: `
                            <b>Name:</b> <a href="${url}" target="_blank" style="color: lightblue; text-decoration: underline;">${name}</a><br>
                            <b>Age:</b> ${age} Ma<br>
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

        function formatMass(mass) {
            if (mass === 'Unknown' || isNaN(mass)) return 'Unknown';
            if (mass > 500) {
                return (mass / 1000).toFixed(2) + ' kg';
            } else {
                return mass + ' g';
            }
        }

        function getCraterSize(diameter) {
            if (diameter >= 50) return 25;
            if (diameter >= 30) return 20;
            if (diameter >= 10) return 15;
            return 10;
        }

        function updateTopMeteorites() {
            const sortedMeteorites = filteredMeteorites.filter(m => m.mass).sort((a, b) => parseFloat(b.mass) - parseFloat(a.mass));
            const top10 = sortedMeteorites.slice(0, 10);
            const bar = document.getElementById('meteoriteBar');
            bar.innerHTML = '<div class="bar-item"><strong>Top Meteorites:</strong></div>';

            top10.forEach((meteorite) => {
                const originalIndex = filteredMeteorites.indexOf(meteorite);
                const name = meteorite.name || 'Unknown';
                const mass = parseFloat(meteorite.mass) || 0;
                const massDisplay = formatMass(mass);
                const div = document.createElement('div');
                div.className = 'bar-item';
                div.innerText = `🌠 ${name} - ${massDisplay}`;
                div.onclick = () => flyToMeteorite(originalIndex);
                bar.appendChild(div);
            });

            const viewAll = document.createElement('div');
            viewAll.className = 'bar-item';
            viewAll.innerHTML = `<strong>View All</strong>`;
            viewAll.onclick = () => openModal();
            bar.appendChild(viewAll);
        }

        function updateTopCraters() {
            const sortedCraters = filteredCraters.filter(c => c.properties.diameter_km).sort((a, b) => b.properties.diameter_km - a.properties.diameter_km);
            const top10 = sortedCraters.slice(0, 10);
            const bar = document.getElementById('craterBar');
            bar.innerHTML = '<div class="bar-item"><strong>Top Craters:</strong></div>';

            top10.forEach((crater) => {
                const originalIndex = filteredCraters.indexOf(crater);
                const name = crater.properties.crater_name || 'Unknown';
                const diameter = crater.properties.diameter_km || 0;
                const div = document.createElement('div');
                div.className = 'bar-item';
                div.innerText = `☄️ ${name} - ${diameter} km`;
                div.onclick = () => flyToCrater(originalIndex);
                bar.appendChild(div);
            });

            const viewAllCraters = document.createElement('div');
            viewAllCraters.className = 'bar-item';
            viewAllCraters.innerHTML = `<strong>View All Craters</strong>`;
            viewAllCraters.onclick = () => openCraterModal();
            bar.appendChild(viewAllCraters);
        }

        function flyToMeteorite(index) {
            const meteorite = filteredMeteorites[index];
            if (!meteorite) {
                console.error('Invalid meteorite index:', index);
                return;
            }
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
                    destination: Cesium.Cartesian3.fromDegrees(lon, lat, 1000000),
                    duration: 2,
                    orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(270) }
                });
            }
        }

        function flyToCrater(index) {
            const crater = filteredCraters[index];
            if (!crater) {
                console.error('Invalid crater index:', index);
                return;
            }
            const geometry = crater.geometry;
            if (geometry && geometry.type === "Point") {
                const [lon, lat] = geometry.coordinates;
                viewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(lon, lat, 1000000),
                    duration: 2,
                    orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(270) }
                });
            }
        }

        const tooltip = document.getElementById('tooltip');
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

        handler.setInputAction(movement => {
            const picked = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(picked)) {
                if (picked.id.isMeteorite || picked.id.isImpactCrater) {
                    tooltip.style.display = 'block';
                    tooltip.innerHTML = picked.id.description.getValue();
                    updateTooltipPosition(movement.endPosition);
                } else {
                    tooltip.style.display = 'none';
                }
            } else {
                tooltip.style.display = 'none';
            }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

        handler.setInputAction(() => { tooltip.style.display = 'none'; }, Cesium.ScreenSpaceEventType.LEFT_DOWN);

        function updateTooltipPosition(position) {
            const x = position.x + 15;
            const y = position.y + 15;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        // Modal Elements
        const modal = document.getElementById('modal');
        const closeModal = document.getElementById('closeModal');

        const craterModal = document.getElementById('craterModal');
        const closeCraterModal = document.getElementById('closeCraterModal');

        const infoModal = document.getElementById('infoModal');
        const infoButton = document.getElementById('infoButton');
        const closeInfoModal = document.getElementById('closeInfoModal');

        closeModal.onclick = () => modal.style.display = 'none';
        closeCraterModal.onclick = () => craterModal.style.display = 'none';
        closeInfoModal.onclick = () => infoModal.style.display = 'none';

        window.onclick = event => {
            if (event.target == modal) modal.style.display = 'none';
            if (event.target == craterModal) craterModal.style.display = 'none';
            if (event.target == infoModal) infoModal.style.display = 'none';
        };

        function openModal() {
            const tbody = document.querySelector('#fullMeteoriteTable tbody');
            if (!filteredMeteorites.length) {
                tbody.innerHTML = '<tr><td colspan="5">No meteorite data available.</td></tr>';
                return;
            }
            tbody.innerHTML = filteredMeteorites.map((meteorite, index) => {
                const name = meteorite.name || 'Unknown';
                const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                const massDisplay = formatMass(mass);
                const recclass = meteorite.recclass || 'Unknown';
                const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                const fall = meteorite.fall || 'Unknown';
                return `
                    <tr onclick='flyToMeteorite(${index})' style="cursor:pointer;">
                        <td>${name}</td>
                        <td>${massDisplay}</td>
                        <td>${recclass}</td>
                        <td>${year}</td>
                        <td>${fall}</td>
                    </tr>
                `;
            }).join('');
            modal.style.display = 'block';
        }

        function openCraterModal() {
            const tbody = document.querySelector('#fullCraterTable tbody');
            if (!filteredCraters.length) {
                tbody.innerHTML = '<tr><td colspan="5">No crater data available.</td></tr>';
                return;
            }
            tbody.innerHTML = filteredCraters.map((crater, index) => {
                const name = crater.properties.crater_name || 'Unknown';
                const diameter = crater.properties.diameter_km || 'Unknown';
                const age = crater.properties.age_millions_years_ago || 'Unknown';
                const country = crater.properties.country || 'Unknown';
                const targetRock = crater.properties.target_rock || 'Unknown';
                return `
                    <tr onclick='flyToCrater(${index})' style="cursor:pointer;">
                        <td>${name}</td>
                        <td>${diameter} km</td>
                        <td>${age} Ma</td>
                        <td>${country}</td>
                        <td>${targetRock}</td>
                    </tr>
                `;
            }).join('');
            craterModal.style.display = 'block';
        }

        window.flyToMeteorite = flyToMeteorite;
        window.flyToCrater = flyToCrater;

        document.getElementById('searchButton').onclick = searchLocation;
        document.getElementById('searchInput').onkeydown = e => { if (e.key === 'Enter') searchLocation(); };

        function searchLocation() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length) {
                        const { lon, lat } = data[0];
                        viewer.camera.flyTo({
                            destination: Cesium.Cartesian3.fromDegrees(parseFloat(lon), parseFloat(lat), 1000000),
                            duration: 2,
                            orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(270) }
                        });
                    } else {
                        alert('Location not found.');
                    }
                })
                .catch(error => {
                    console.error('Error searching location:', error);
                });
        }

        document.getElementById('basemapSelector').onchange = function() {
            const selectedBasemap = this.value;
            while (viewer.imageryLayers.length > 1) {
                viewer.imageryLayers.remove(viewer.imageryLayers.get(1));
            }
            switch(selectedBasemap) {
                case 'OpenStreetMap':
                    viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({
                        url : 'https://a.tile.openstreetmap.org/'
                    }));
                    break;
                case 'Cesium World Imagery':
                default:
                    viewer.imageryLayers.addImageryProvider(new Cesium.IonImageryProvider({ assetId: 2 }));
            }
        };

        document.getElementById('basemapSelector').value = 'Cesium World Imagery';

        document.getElementById('yearRangeMin').addEventListener('input', () => {
            applyFilters();
            updateSlidersDisplay();
        });
        document.getElementById('yearRangeMax').addEventListener('input', () => {
            applyFilters();
            updateSlidersDisplay();
        });
        document.getElementById('massRangeMin').addEventListener('input', () => {
            applyFilters();
            updateSlidersDisplay();
        });
        document.getElementById('massRangeMax').addEventListener('input', () => {
            applyFilters();
            updateSlidersDisplay();
        });

        document.getElementById('diameterRangeMin').addEventListener('input', () => {
            applyFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('diameterRangeMax').addEventListener('input', () => {
            applyFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('ageRangeMin').addEventListener('input', () => {
            applyFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('ageRangeMax').addEventListener('input', () => {
            applyFilters();
            updateCraterSlidersDisplay();
        });
        document.getElementById('targetRockSelect').addEventListener('change', () => {
            applyFilters();
        });

        document.getElementById('toggleMeteorites').addEventListener('change', function() {
            meteoriteEntities.show = this.checked;
        });

        document.getElementById('toggleCraters').addEventListener('change', function() {
            craterEntities.show = this.checked;
        });

        document.getElementById('refreshButton').onclick = resetFilters;

        function resetFilters() {
            document.getElementById('yearRangeMin').value = 860;
            document.getElementById('yearRangeMax').value = 2023;
            document.getElementById('massRangeMin').value = 0;
            document.getElementById('massRangeMax').value = 60000;

            document.getElementById('diameterRangeMin').value = 0;
            document.getElementById('diameterRangeMax').value = 300;
            document.getElementById('ageRangeMin').value = 0;
            document.getElementById('ageRangeMax').value = 2000;

            const targetRockSelect = document.getElementById('targetRockSelect');
            for (let i = 0; i < targetRockSelect.options.length; i++) {
                targetRockSelect.options[i].selected = false;
            }

            applyFilters();

            updateSlidersDisplay();
            updateCraterSlidersDisplay();
        }

        function updateSlidersDisplay() {
            const yearMin = parseInt(document.getElementById('yearRangeMin').value);
            const yearMax = parseInt(document.getElementById('yearRangeMax').value);
            document.getElementById('yearRangeValue').innerText = `${yearMin} - ${yearMax} Ma`;

            const massMin = parseInt(document.getElementById('massRangeMin').value);
            const massMax = parseInt(document.getElementById('massRangeMax').value);
            document.getElementById('massRangeValue').innerText = `${formatMass(massMin)} - ${formatMass(massMax)}`;
        }

        function updateCraterSlidersDisplay() {
            const diameterMin = parseInt(document.getElementById('diameterRangeMin').value);
            const diameterMax = parseInt(document.getElementById('diameterRangeMax').value);
            document.getElementById('diameterRangeValue').innerText = `${diameterMin} - ${diameterMax} km`;

            const ageMin = parseInt(document.getElementById('ageRangeMin').value);
            const ageMax = parseInt(document.getElementById('ageRangeMax').value);
            document.getElementById('ageRangeValue').innerText = `${ageMin} - ${ageMax} Ma`;
        }

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

        function updateMeteoriteModalTable() {
            const tbody = document.querySelector('#fullMeteoriteTable tbody');
            if (!filteredMeteorites.length) {
                tbody.innerHTML = '<tr><td colspan="5">No meteorite data available.</td></tr>';
                return;
            }
            tbody.innerHTML = filteredMeteorites.map((meteorite, index) => {
                const name = meteorite.name || 'Unknown';
                const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                const massDisplay = formatMass(mass);
                const recclass = meteorite.recclass || 'Unknown';
                const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                const fall = meteorite.fall || 'Unknown';
                return `
                    <tr onclick='flyToMeteorite(${index})' style="cursor:pointer;">
                        <td>${name}</td>
                        <td>${massDisplay}</td>
                        <td>${recclass}</td>
                        <td>${year}</td>
                        <td>${fall}</td>
                    </tr>
                `;
            }).join('');
        }

        function updateCraterModalTable() {
            const tbody = document.querySelector('#fullCraterTable tbody');
            if (!filteredCraters.length) {
                tbody.innerHTML = '<tr><td colspan="5">No crater data available.</td></tr>';
                return;
            }
            tbody.innerHTML = filteredCraters.map((crater, index) => {
                const name = crater.properties.crater_name || 'Unknown';
                const diameter = crater.properties.diameter_km || 'Unknown';
                const age = crater.properties.age_millions_years_ago || 'Unknown';
                const country = crater.properties.country || 'Unknown';
                const targetRock = crater.properties.target_rock || 'Unknown';
                return `
                    <tr onclick='flyToCrater(${index})' style="cursor:pointer;">
                        <td>${name}</td>
                        <td>${diameter} km</td>
                        <td>${age} Ma</td>
                        <td>${country}</td>
                        <td>${targetRock}</td>
                    </tr>
                `;
            }).join('');
        }

        function initializeCraterFilters() {
            populateTargetRockOptions();
        }

        function initializeSliders() {
            updateSlidersDisplay();
            updateCraterSlidersDisplay();
        }

        initializeSliders();
        initializeCraterFilters();

        fetchAllMeteorites();

        const closeOptionsButton = document.getElementById('closeOptions');
        closeOptionsButton.onclick = () => {
            const controls = document.getElementById('controls');
            controls.style.display = 'none';
        };

        const optionsButton = document.getElementById('optionsButton');
        const controls = document.getElementById('controls');

        optionsButton.onclick = () => {
            if (controls.style.display === 'none' || controls.style.display === '') {
                controls.style.display = 'block';
            } else {
                controls.style.display = 'none';
            }
        };
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
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
