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
    <title>🌠 Global Meteorite Specimens & Impact Craters 🌠</title>
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
            top: 100px;
            left: 10px;
            background: rgba(0, 0, 0, 0.9);
            padding: 30px 10px 10px 10px;
            z-index: 1000;
            color: white;
            border-radius: 5px;
            max-height: calc(100% - 120px);
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
            background: rgba(0, 0, 0, 1);
            display: flex;
            overflow-x: auto;
            padding: 5px 0;
            z-index: 1;
        }
        #craterBar {
            bottom: 40px;
        }
        #meteoriteBar {
            bottom: 0;
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
        #modal, #infoModal, #craterModal, #keyModal {
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
        #modal-content, #infoModal-content, #craterModal-content, #keyModal-content {
            background-color: #2b2b2b;
            margin: 5% auto;
            padding: 20px;
            width: 80%;
            color: white;
            border-radius: 5px;
            position: relative;
        }
        #closeModal, #closeInfoModal, #closeCraterModal, #closeKeyModal, #controls .close-button {
            color: #aaa;
            position: absolute;
            top: 10px;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        #closeModal:hover, #closeModal:focus, #closeInfoModal:hover, #closeInfoModal:focus, #closeCraterModal:hover, #closeCraterModal:focus, #closeKeyModal:hover, #closeKeyModal:focus, #controls .close-button:hover, #controls .close-button:focus {
            color: white;
            text-decoration: none;
        }
        #fullMeteoriteTable, #fullCraterTable {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        #fullMeteoriteTable th, #fullMeteoriteTable td,
        #fullCraterTable th, #fullCraterTable td {
            border: 1px solid #444;
            padding: 8px;
            text-align: left;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        #fullMeteoriteTable th, #fullCraterTable th {
            background-color: #555;
            position: sticky;
            top: 0;
            z-index: 500;
            cursor: pointer;
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
        #modal-content, #craterModal-content, #keyModal-content {
            max-height: 80vh;
            overflow: hidden;
        }
        #fullMeteoriteTable tbody, #fullCraterTable tbody {
            display: block;
            max-height: 60vh;
            overflow-y: auto;
        }
        #fullMeteoriteTable thead, #fullCraterTable thead {
            display: table;
            width: 100%;
            table-layout: fixed;
        }
        #fullMeteoriteTable tbody tr, #fullCraterTable tbody tr {
            display: table;
            width: 100%;
            table-layout: fixed;
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="header">
        <h1>🌠 Global Meteorite Specimens & Impact Craters 🌠</h1>
        <div>
            <button id="optionsButton">⚙️ Options</button>
            <button id="keyButton">🗝️ Key</button>
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
            <input type="range" id="massRangeMin" min="0" max="1000000" value="0">
            <input type="range" id="massRangeMax" min="0" max="1000000" value="1000000">
        </div>
        <div>
            <label><input type="checkbox" id="clusterMeteorites" checked> Enable Clustering</label>
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
            <span id="totalCraters">Total Craters: 0</span>
        </div>
        <div>
            <button id="infoButton">ℹ️ Info</button>
        </div>
    </div>
    <div id="craterBar"></div>
    <div id="meteoriteBar"></div>
    <div id="tooltip"></div>
    <div id="modal">
        <div id="modal-content">
            <span id="closeModal">&times;</span>
            <h2>All Meteorites</h2>
            <table id="fullMeteoriteTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('fullMeteoriteTable', 0)">Name &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullMeteoriteTable', 1)">Mass &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullMeteoriteTable', 2)">Class &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullMeteoriteTable', 3)">Year &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullMeteoriteTable', 4)">Fall/Find &#x25B2;&#x25BC;</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
    <div id="craterModal">
        <div id="craterModal-content">
            <span id="closeCraterModal">&times;</span>
            <h2>All Impact Craters</h2>
            <table id="fullCraterTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('fullCraterTable', 0)">Name &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullCraterTable', 1)">Diameter (km) &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullCraterTable', 2)">Age (Ma) &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullCraterTable', 3)">Country &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullCraterTable', 4)">Exposed &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullCraterTable', 5)">Drilled &#x25B2;&#x25BC;</th>
                        <th onclick="sortTable('fullCraterTable', 6)">Bolide Type &#x25B2;&#x25BC;</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
    <div id="infoModal">
        <div id="infoModal-content">
            <span id="closeInfoModal">&times;</span>
            <h2>Information</h2>
            <p>Welcome to the Global Meteorite Specimens and Impact Craters Visualization. This interactive tool allows you to explore meteorite landings recorded by NASA and discover impact craters around the world.</p>
            <h3>How to Use:</h3>
            <ul>
                <li><strong>Navigation:</strong> Use your mouse or touch controls to navigate around the globe.</li>
                <li><strong>Search:</strong> Use the search bar to fly to a specific location.</li>
                <li><strong>Filters:</strong> Adjust the sliders and dropdowns in the controls menu to filter meteorites and craters based on various criteria such as year, mass, diameter, age, and target rock type.</li>
                <li><strong>Show/Hide Data:</strong> Toggle the visibility of meteorites and craters using the checkboxes.</li>
                <li><strong>Reset Filters:</strong> Click the "Reset Filters" button to return all filters to their default settings.</li>
                <li><strong>Top Meteorites:</strong> View the top meteorites by mass at the bottom bar and click on them to fly to their location.</li>
                <li><strong>Top Impact Craters:</strong> View the top impact craters by diameter in the bar above and click on them to fly to their location.</li>
                <li><strong>Details:</strong> Click on any meteorite or crater marker to view detailed information.</li>
                <li><strong>View All:</strong> Click on "View All" in the top meteorites or craters bar to see a full list.</li>
            </ul>
            <h3>Data Sources:</h3>
            <ul>
                <li><a href="https://data.nasa.gov/Space-Science/Meteorite-Landings/gh4g-9sfh" target="_blank">NASA Meteorite Landings Dataset</a></li>
                <li><a href="https://github.com/Antash/earth-impact-db" target="_blank">Earth Impact Database via Antash</a></li>
            </ul>
            <p>This application utilizes CesiumJS for 3D globe visualization.</p>
        </div>
    </div>
    <div id="keyModal">
        <div id="keyModal-content">
            <span id="closeKeyModal">&times;</span>
            <h2>Key</h2>
            <h3>Meteorite Symbols:</h3>
            <p>The size of the meteorite symbol correlates with its mass, and the color indicates its mass range:</p>
            <ul>
                <li><span style="color: purple;">●</span> Large purple circle (size 20 px): Mass ≥ 500,000 g</li>
                <li><span style="color: red;">●</span> Large red circle (size 15 px): 100,000 g ≤ Mass &lt; 500,000 g</li>
                <li><span style="color: orange;">●</span> Medium orange circle (size 10 px): 50,000 g ≤ Mass &lt; 100,000 g</li>
                <li><span style="color: yellow;">●</span> Small yellow circle (size 7 px): 10,000 g ≤ Mass &lt; 50,000 g</li>
                <li><span style="color: cyan;">●</span> Tiny cyan circle (size 5 px): Mass &lt; 10,000 g</li>
            </ul>
            <h3>Impact Crater Symbols:</h3>
            <p>The size of the impact crater symbol correlates with its diameter, and the color indicates its diameter range:</p>
            <ul>
                <li><span style="color: navy;">▲</span> Large navy triangle (size 25 px): Diameter ≥ 50 km</li>
                <li><span style="color: darkblue;">▲</span> Medium dark blue triangle (size 20 px): 30 km ≤ Diameter &lt; 50 km</li>
                <li><span style="color: blue;">▲</span> Small blue triangle (size 15 px): 10 km ≤ Diameter &lt; 30 km</li>
                <li><span style="color: lightblue;">▲</span> Tiny light blue triangle (size 10 px): Diameter &lt; 10 km</li>
            </ul>
        </div>
    </div>
    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: false,
            navigationHelpButton: true,
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

        let allMeteorites = [];
        let filteredMeteorites = [];
        const impactCraters = {{ impact_craters | tojson }};
        let filteredCraters = [];
        const allCraters = impactCraters.features;

        let meteoritePoints = viewer.scene.primitives.add(new Cesium.PointPrimitiveCollection());
        let craterEntities = new Cesium.CustomDataSource('craters');
        viewer.dataSources.add(craterEntities);

        // Enhanced clustering parameters
        const clusterOptions = {
            enabled: true,
            pixelRange: 50,
            minimumClusterSize: 5
        };

        const entityCluster = new Cesium.EntityCluster(clusterOptions);

        function getMeteoriteColor(mass) {
            if (mass >= 500000) return Cesium.Color.RED.withAlpha(0.6);
            if (mass >= 100000) return Cesium.Color.ORANGE.withAlpha(0.6);
            if (mass >= 50000)  return Cesium.Color.YELLOW.withAlpha(0.6);
            if (mass >= 10000)  return Cesium.Color.GREEN.withAlpha(0.6);
            return Cesium.Color.CYAN.withAlpha(0.6);
        }

        function getCraterColor(diameter) {
            if (diameter >= 50) return Cesium.Color.NAVY.withAlpha(0.8);
            if (diameter >= 30) return Cesium.Color.DARKBLUE.withAlpha(0.8);
            if (diameter >= 10) return Cesium.Color.BLUE.withAlpha(0.8);
            return Cesium.Color.LIGHTBLUE.withAlpha(0.8);
        }

        function fetchAllMeteorites() {
            const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=50000';
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
            updateTopCraters();
            updateTotalCounts();
            updateModalTable();
            updateCraterModalTable();
        }

        function updateTotalCounts() {
            document.getElementById('totalMeteorites').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
            document.getElementById('totalCraters').innerText = `Total Craters: ${filteredCraters.length}`;
        }

        function updateMeteoriteData() {
            meteoritePoints.removeAll();

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
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                    meteoritePoints.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 10000, 5), 20) : 5,
                        color: mass !== 'Unknown' ? getMeteoriteColor(mass) : Cesium.Color.GRAY.withAlpha(0.6),
                        id: {
                            isMeteorite: true,
                            meteoriteIndex: index
                        }
                    });
                }
            });

            meteoritePoints.cluster = new Cesium.EntityCluster({
                enabled: document.getElementById('clusterMeteorites').checked,
                pixelRange: 50,
                minimumClusterSize: 5
            });
        }

        function updateCraterData() {
            craterEntities.entities.removeAll();

            filteredCraters.forEach((feature, index) => {
                const properties = feature.properties;
                const geometry = feature.geometry;

                if (geometry && geometry.type === "Point") {
                    const [lon, lat] = geometry.coordinates;
                    let diameter = parseFloat(properties.diameter_km) || 1;

                    craterEntities.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: getCraterSize(diameter),
                            color: getCraterColor(diameter),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: getCraterDescription(properties),
                        isImpactCrater: true,
                        craterIndex: index
                    });
                }
            });
        }

        function getCraterDescription(properties) {
            const name = properties.crater_name || 'Unknown';
            const age = properties.age_millions_years_ago || 'Unknown';
            const diameter = properties.diameter_km || 'Unknown';
            const country = properties.country || 'Unknown';
            const target_rock = properties.target_rock || 'Unknown';
            const exposed = properties.exposed !== undefined ? properties.exposed : 'Unknown';
            const drilled = properties.drilled !== undefined ? properties.drilled : 'Unknown';
            const bolide_type = properties.bolid_type || 'Unknown';
            const url = properties.url || '#';
            return `
                <b>Name:</b> ${name}<br>
                <b>Age:</b> ${age} Ma<br>
                <b>Diameter:</b> ${diameter} km<br>
                <b>Country:</b> ${country}<br>
                <b>Target Rock:</b> ${target_rock}<br>
                <b>Exposed:</b> ${exposed}<br>
                <b>Drilled:</b> ${drilled}<br>
                <b>Bolide Type:</b> ${bolide_type}<br>
                <b>URL:</b> <a href="${url}" target="_blank">More Info</a>
            `;
        }

        function formatMass(mass) {
            if (mass === 'Unknown' || isNaN(mass)) return 'Unknown';
            if (mass >= 1000000) {
                return (mass / 1000000).toFixed(2) + ' tonnes';
            } else if (mass >= 1000) {
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

            const viewAll = document.createElement('div');
            viewAll.className = 'bar-item';
            viewAll.innerHTML = `<strong>View All</strong>`;
            viewAll.onclick = () => openModal();
            bar.appendChild(viewAll);

            top10.forEach((meteorite, index) => {
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
        }

        function updateTopCraters() {
            const sortedCraters = filteredCraters.filter(c => c.properties.diameter_km).sort((a, b) => parseFloat(b.properties.diameter_km) - parseFloat(a.properties.diameter_km));
            const top10Craters = sortedCraters.slice(0, 10);
            const craterBar = document.getElementById('craterBar');
            craterBar.innerHTML = '<div class="bar-item"><strong>Top Impact Craters:</strong></div>';

            const viewAllCraters = document.createElement('div');
            viewAllCraters.className = 'bar-item';
            viewAllCraters.innerHTML = `<strong>View All</strong>`;
            viewAllCraters.onclick = () => openCraterModal();
            craterBar.appendChild(viewAllCraters);

            top10Craters.forEach((crater, index) => {
                const name = crater.properties.crater_name || 'Unknown';
                const diameter = parseFloat(crater.properties.diameter_km) || 0;
                const diameterDisplay = diameter ? `${diameter} km` : 'Unknown';
                const div = document.createElement('div');
                div.className = 'bar-item';
                div.innerText = `💥 ${name} - ${diameterDisplay}`;
                div.onclick = () => flyToCrater(filteredCraters.indexOf(crater));
                craterBar.appendChild(div);
            });
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
            if (!crater) return;

            const [lon, lat] = crater.geometry.coordinates;

            viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(lon, lat, 1000000),
                duration: 2,
                orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(-45) }
            });
        }

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
            document.getElementById('modal').style.display = 'block';
        }

        function openCraterModal() {
            const tbody = document.querySelector('#fullCraterTable tbody');
            if (!filteredCraters.length) {
                tbody.innerHTML = '<tr><td colspan="8">No crater data available.</td></tr>';
                return;
            }
            tbody.innerHTML = filteredCraters.map((crater, index) => {
                const name = crater.properties.crater_name || 'Unknown';
                const diameter = parseFloat(crater.properties.diameter_km) || 'Unknown';
                const age = crater.properties.age_millions_years_ago || 'Unknown';
                const country = crater.properties.country || 'Unknown';
                const exposed = crater.properties.exposed !== undefined ? crater.properties.exposed : 'Unknown';
                const drilled = crater.properties.drilled !== undefined ? crater.properties.drilled : 'Unknown';
                const bolide_type = crater.properties.bolid_type || 'Unknown';
                const url = crater.properties.url || '#';
                return `
                    <tr>
                        <td>${name}</td>
                        <td>${diameter}</td>
                        <td>${age}</td>
                        <td>${country}</td>
                        <td>${exposed}</td>
                        <td>${drilled}</td>
                        <td>${bolide_type}</td>
                        <td><a href="${url}" target="_blank">Visit</a></td>
                    </tr>
                `;
            }).join('');
            document.getElementById('craterModal').style.display = 'block';
        }

        const tooltip = document.getElementById('tooltip');
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

        handler.setInputAction(movement => {
            const pickedObject = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(pickedObject)) {
                if (pickedObject.id && (pickedObject.id.isMeteorite || pickedObject.id.isImpactCrater)) {
                    tooltip.style.display = 'block';
                    if (pickedObject.id.isImpactCrater) {
                        tooltip.innerHTML = pickedObject.id.description.getValue();
                    } else if (pickedObject.id.isMeteorite) {
                        const index = pickedObject.id.meteoriteIndex;
                        const meteorite = filteredMeteorites[index];
                        tooltip.innerHTML = getMeteoriteDescription(meteorite);
                    }
                    updateTooltipPosition(movement.endPosition);
                } else {
                    tooltip.style.display = 'none';
                }
            } else {
                tooltip.style.display = 'none';
            }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

        function getMeteoriteDescription(meteorite) {
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

            const name = meteorite.name || 'Unknown';
            const id = meteorite.id || 'Unknown';
            const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
            const massDisplay = formatMass(mass);
            const recclass = meteorite.recclass || 'Unknown';
            const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
            const fall = meteorite.fall || 'Unknown';

            return `
                <b>Name:</b> ${name}<br>
                <b>ID:</b> ${id}<br>
                <b>Latitude:</b> ${lat ? lat.toFixed(5) : 'Unknown'}<br>
                <b>Longitude:</b> ${lon ? lon.toFixed(5) : 'Unknown'}<br>
                <b>Mass:</b> ${massDisplay}<br>
                <b>Class:</b> ${recclass}<br>
                <b>Year:</b> ${year}<br>
                <b>Fall/Find:</b> ${fall}
            `;
        }

        function updateTooltipPosition(position) {
            const x = position.x + 15;
            const y = position.y + 15;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        const modal = document.getElementById('modal');
        const craterModal = document.getElementById('craterModal');
        const keyModal = document.getElementById('keyModal');
        const infoModal = document.getElementById('infoModal');
        document.getElementById('closeModal').onclick = () => modal.style.display = 'none';
        document.getElementById('closeCraterModal').onclick = () => craterModal.style.display = 'none';
        document.getElementById('closeKeyModal').onclick = () => keyModal.style.display = 'none';
        document.getElementById('closeInfoModal').onclick = () => infoModal.style.display = 'none';
        window.onclick = event => {
            if (event.target == modal) modal.style.display = 'none';
            if (event.target == craterModal) craterModal.style.display = 'none';
            if (event.target == infoModal) infoModal.style.display = 'none';
            if (event.target == keyModal) keyModal.style.display = 'none';
        };

        function updateModalTable() {
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
                tbody.innerHTML = '<tr><td colspan="8">No crater data available.</td></tr>';
                return;
            }
            tbody.innerHTML = filteredCraters.map((crater, index) => {
                const name = crater.properties.crater_name || 'Unknown';
                const diameter = parseFloat(crater.properties.diameter_km) || 'Unknown';
                const age = crater.properties.age_millions_years_ago || 'Unknown';
                const country = crater.properties.country || 'Unknown';
                const exposed = crater.properties.exposed !== undefined ? crater.properties.exposed : 'Unknown';
                const drilled = crater.properties.drilled !== undefined ? crater.properties.drilled : 'Unknown';
                const bolide_type = crater.properties.bolid_type || 'Unknown';
                const url = crater.properties.url || '#';
                return `
                    <tr>
                        <td>${name}</td>
                        <td>${diameter}</td>
                        <td>${age}</td>
                        <td>${country}</td>
                        <td>${exposed}</td>
                        <td>${drilled}</td>
                        <td>${bolide_type}</td>
                        <td><a href="${url}" target="_blank">Visit</a></td>
                    </tr>
                `;
            }).join('');
        }

        function sortTable(tableId, colIndex) {
            const table = document.getElementById(tableId);
            let switching = true;
            let dir = "asc";
            let switchcount = 0;

            while (switching) {
                switching = false;
                const rows = table.querySelectorAll("tbody tr");
                for (let i = 0; i < rows.length - 1; i++) {
                    let shouldSwitch = false;
                    const x = rows[i].getElementsByTagName("TD")[colIndex];
                    const y = rows[i + 1].getElementsByTagName("TD")[colIndex];
                    let xContent = x.textContent || x.innerText;
                    let yContent = y.textContent || y.innerText;

                    const xNum = parseFloat(xContent.replace(/[^\d.-]/g, ''));
                    const yNum = parseFloat(yContent.replace(/[^\d.-]/g, ''));

                    if (!isNaN(xNum) && !isNaN(yNum)) {
                        if (dir == "asc") {
                            if (xNum > yNum) {
                                shouldSwitch = true;
                                break;
                            }
                        } else if (dir == "desc") {
                            if (xNum < yNum) {
                                shouldSwitch = true;
                                break;
                            }
                        }
                    } else {
                        if (dir == "asc") {
                            if (xContent.toLowerCase() > yContent.toLowerCase()) {
                                shouldSwitch = true;
                                break;
                            }
                        } else if (dir == "desc") {
                            if (xContent.toLowerCase() < yContent.toLowerCase()) {
                                shouldSwitch = true;
                                break;
                            }
                        }
                    }
                }
                if (shouldSwitch) {
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                } else {
                    if (switchcount == 0 && dir == "asc") {
                        dir = "desc";
                        switching = true;
                    }
                }
            }
        }

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
            meteoritePoints.show = this.checked;
        });

        document.getElementById('clusterMeteorites').addEventListener('change', function() {
            meteoritePoints.cluster.enabled = this.checked;
        });

        document.getElementById('toggleCraters').addEventListener('change', function() {
            craterEntities.show = this.checked;
        });

        document.getElementById('refreshButton').onclick = resetFilters;

        function resetFilters() {
            document.getElementById('yearRangeMin').value = 860;
            document.getElementById('yearRangeMax').value = 2023;
            document.getElementById('massRangeMin').value = 0;
            document.getElementById('massRangeMax').value = 1000000;

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
            document.getElementById('yearRangeValue').innerText = `${yearMin} - ${yearMax}`;

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

        const infoModal = document.getElementById('infoModal');
        const infoButton = document.getElementById('infoButton');
        const closeInfoModal = document.getElementById('closeInfoModal');

        infoButton.onclick = () => {
            infoModal.style.display = 'block';
        };

        closeInfoModal.onclick = () => {
            infoModal.style.display = 'none';
        };

        window.flyToCrater = flyToCrater;

        const optionsButton = document.getElementById('optionsButton');
        const controls = document.getElementById('controls');
        const closeOptions = document.getElementById('closeOptions');

        optionsButton.onclick = () => {
            if (controls.style.display === 'none' || controls.style.display === '') {
                controls.style.display = 'block';
            } else {
                controls.style.display = 'none';
            }
        };

        closeOptions.onclick = () => {
            controls.style.display = 'none';
        };

        // Key Modal Functionality
        const keyButton = document.getElementById('keyButton');
        const keyModalElement = document.getElementById('keyModal');
        const closeKeyModal = document.getElementById('closeKeyModal');

        keyButton.onclick = () => {
            keyModalElement.style.display = 'block';
        };

        closeKeyModal.onclick = () => {
            keyModalElement.style.display = 'none';
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
