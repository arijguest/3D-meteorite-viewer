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
        /* Key menu styles */
        #keyMenu {
            position: absolute;
            top: 100px;
            left: 320px;
            background: rgba(0, 0, 0, 0.9);
            padding: 30px 10px 10px 10px;
            z-index: 1000;
            color: white;
            border-radius: 5px;
            max-height: calc(100% - 120px);
            overflow-y: auto;
            display: none;
            width: 250px;
        }
        #keyMenu .close-button {
            position: absolute;
            top: 10px;
            right: 10px;
            background: transparent;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
        }
        .key-circle {
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
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
        #modal, #infoModal, #craterModal {
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
        #modal-content, #infoModal-content, #craterModal-content {
            background-color: #2b2b2b;
            margin: 5% auto;
            padding: 20px;
            width: 80%;
            color: white;
            border-radius: 5px;
            position: relative;
        }
        #closeModal, #closeInfoModal, #closeCraterModal, #controls .close-button {
            color: #aaa;
            position: absolute;
            top: 10px;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            right: 10px;
            background: transparent;
            border: none;
        }
        #closeModal:hover, #closeModal:focus, #closeInfoModal:hover, #closeInfoModal:focus, #closeCraterModal:hover, #closeCraterModal:focus, #controls .close-button:hover, #controls .close-button:focus {
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
        #modal-content, #craterModal-content {
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
            <button id="keyButton">🔑 Key</button>
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
            <label><strong>Age Range (Ma):</strong> <span id="ageRangeValue"></span></label>
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
    <!-- New key menu -->
    <div id="keyMenu">
        <button class="close-button" id="closeKey">&times;</button>
        <h3>Map Key</h3>
        <div>
            <h4>Meteorites:</h4>
            <p><span class="key-circle" style="background-color: cyan;"></span> Mass &lt; 10,000 g</p>
            <p><span class="key-circle" style="background-color: green;"></span> Mass ≥ 10,000 g</p>
            <p><span class="key-circle" style="background-color: yellow;"></span> Mass ≥ 50,000 g</p>
            <p><span class="key-circle" style="background-color: orange;"></span> Mass ≥ 100,000 g</p>
            <p><span class="key-circle" style="background-color: red;"></span> Mass ≥ 500,000 g</p>
        </div>
        <div>
            <h4>Impact Craters:</h4>
            <p><span class="key-circle" style="background-color: lightblue;"></span> Diameter &lt; 10 km</p>
            <p><span class="key-circle" style="background-color: blue;"></span> Diameter ≥ 10 km</p>
            <p><span class="key-circle" style="background-color: darkblue;"></span> Diameter ≥ 30 km</p>
            <p><span class="key-circle" style="background-color: navy;"></span> Diameter ≥ 50 km</p>
        </div>
    </div>
    <div id="craterBar"></div>
    <div id="meteoriteBar"></div>
    <div id="tooltip"></div>
    <div id="modal">
        <div id="modal-content">
            <button id="closeModal">&times;</button>
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
            <button id="closeCraterModal">&times;</button>
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
            <button id="closeInfoModal">&times;</button>
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
    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: true,
            navigationHelpButton: true,
            sceneModePicker: true,
            animation: false,
            timeline: false,
            fullscreenButton: true,
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

        const clusterOptions = {
            enabled: true,
            pixelRange: 50,
            minimumClusterSize: 10
        };

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
            filteredMeteorites = allMeteorites.filter(meteorite => {
                if (!meteorite.geolocation) return false;

                const mass = parseFloat(meteorite.mass) || 0;
                const year = new Date(meteorite.year).getFullYear() || 0;

                if (mass < massMin || mass > massMax) return false;
                if (year < yearMin || year > yearMax) return false;

                return true;
            });

            updateMeteoritePoints();
            updateTopMeteoritesBar();
            document.getElementById('totalMeteorites').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
        }

        function updateMeteoritePoints() {
            meteoritePoints.removeAll();

            if (!toggleMeteoritesCheckbox.checked) return;

            filteredMeteorites.forEach(meteorite => {
                const mass = parseFloat(meteorite.mass) || 0;
                const coords = meteorite.geolocation.coordinates;
                const color = getMeteoriteColor(mass);

                const point = meteoritePoints.add({
                    position: Cesium.Cartesian3.fromDegrees(coords[0], coords[1]),
                    color: color,
                    pixelSize: 5,
                    id: meteorite
                });
            });
        }

        function applyCraterFilters() {
            filteredCraters = allCraters.filter(crater => {
                const diameter = crater.properties.diameter_km || 0;
                const ageMin = crater.properties.age_min || 0;
                const ageMax = crater.properties.age_max || 2000;
                const targetRock = crater.properties.target_rock || '';

                if (diameter < diameterMin || diameter > diameterMax) return false;
                if (ageMax < ageMinValue || ageMin > ageMaxValue) return false;
                if (selectedTargetRocks.length > 0 && !selectedTargetRocks.includes(targetRock)) return false;

                return true;
            });

            updateCraterEntities();
            updateTopCratersBar();
            document.getElementById('totalCraters').innerText = `Total Craters: ${filteredCraters.length}`;
        }

        function updateCraterEntities() {
            craterEntities.entities.removeAll();

            if (!toggleCratersCheckbox.checked) return;

            filteredCraters.forEach(crater => {
                const coords = crater.geometry.coordinates;
                const diameter = crater.properties.diameter_km || 0;
                const color = getCraterColor(diameter);

                const entity = craterEntities.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(coords[0], coords[1]),
                    point: {
                        pixelSize: 8,
                        color: color,
                        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                    },
                    properties: crater.properties
                });
            });
        }

        function updateTopMeteoritesBar() {
            const topMeteorites = [...filteredMeteorites].sort((a, b) => (parseFloat(b.mass) || 0) - (parseFloat(a.mass) || 0)).slice(0, 10);

            meteoriteBar.innerHTML = '';

            topMeteorites.forEach(meteorite => {
                const mass = parseFloat(meteorite.mass) || 0;
                const item = document.createElement('div');
                item.className = 'bar-item';
                item.innerText = `${meteorite.name} (${mass.toLocaleString()} g)`;
                item.onclick = () => {
                    viewer.camera.flyTo({
                        destination: Cesium.Cartesian3.fromDegrees(meteorite.geolocation.coordinates[0], meteorite.geolocation.coordinates[1], 1000000)
                    });
                };
                meteoriteBar.appendChild(item);
            });

            const viewAllButton = document.createElement('div');
            viewAllButton.className = 'bar-item';
            viewAllButton.innerText = 'View All';
            viewAllButton.onclick = () => {
                showMeteoriteModal();
            };
            meteoriteBar.appendChild(viewAllButton);
        }

        function updateTopCratersBar() {
            const topCraters = [...filteredCraters].sort((a, b) => (b.properties.diameter_km || 0) - (a.properties.diameter_km || 0)).slice(0, 10);

            craterBar.innerHTML = '';

            topCraters.forEach(crater => {
                const diameter = crater.properties.diameter_km || 0;
                const item = document.createElement('div');
                item.className = 'bar-item';
                item.innerText = `${crater.properties.name} (${diameter} km)`;
                item.onclick = () => {
                    viewer.camera.flyTo({
                        destination: Cesium.Cartesian3.fromDegrees(crater.geometry.coordinates[0], crater.geometry.coordinates[1], 1000000)
                    });
                };
                craterBar.appendChild(item);
            });

            const viewAllButton = document.createElement('div');
            viewAllButton.className = 'bar-item';
            viewAllButton.innerText = 'View All';
            viewAllButton.onclick = () => {
                showCraterModal();
            };
            craterBar.appendChild(viewAllButton);
        }

        function showMeteoriteModal() {
            const tbody = document.querySelector('#fullMeteoriteTable tbody');
            tbody.innerHTML = '';

            filteredMeteorites.forEach(meteorite => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${meteorite.name}</td>
                    <td>${(parseFloat(meteorite.mass) || 0).toLocaleString()}</td>
                    <td>${meteorite.recclass || ''}</td>
                    <td>${(new Date(meteorite.year)).getFullYear() || ''}</td>
                    <td>${meteorite.fall || ''}</td>
                `;
                tbody.appendChild(tr);
            });

            modal.style.display = 'block';
        }

        function showCraterModal() {
            const tbody = document.querySelector('#fullCraterTable tbody');
            tbody.innerHTML = '';

            filteredCraters.forEach(crater => {
                const props = crater.properties;
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${props.name || ''}</td>
                    <td>${props.diameter_km || ''}</td>
                    <td>${(props.age_ma || '')}</td>
                    <td>${props.country || ''}</td>
                    <td>${props.exposed || ''}</td>
                    <td>${props.drilled || ''}</td>
                    <td>${props.bolide_type || ''}</td>
                    <td><a href="${props.wikilink || '#'}" target="_blank">Link</a></td>
                `;
                tbody.appendChild(tr);
            });

            craterModal.style.display = 'block';
        }

        function sortTable(tableId, colIndex) {
            const table = document.getElementById(tableId);
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.getElementsByTagName('tr'));

            const sortedRows = rows.sort((a, b) => {
                const aText = a.getElementsByTagName('td')[colIndex].innerText;
                const bText = b.getElementsByTagName('td')[colIndex].innerText;

                if (!isNaN(parseFloat(aText)) && !isNaN(parseFloat(bText))) {
                    return parseFloat(aText) - parseFloat(bText);
                }
                return aText.localeCompare(bText);
            });

            tbody.innerHTML = '';
            sortedRows.forEach(row => tbody.appendChild(row));
        }

        function updateBasemap() {
            const selectedBasemap = basemapSelector.value;
            if (selectedBasemap === 'OpenStreetMap') {
                viewer.imageryLayers.removeAll();
                viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider());
            } else {
                viewer.imageryLayers.removeAll();
                viewer.imageryLayers.addImageryProvider(Cesium.createWorldImagery());
            }
        }

        let massMin = 0;
        let massMax = 1000000;
        let yearMin = 860;
        let yearMax = 2023;
        let diameterMin = 0;
        let diameterMax = 300;
        let ageMinValue = 0;
        let ageMaxValue = 2000;
        let selectedTargetRocks = [];

        const toggleMeteoritesCheckbox = document.getElementById('toggleMeteorites');
        const toggleCratersCheckbox = document.getElementById('toggleCraters');
        const clusterMeteoritesCheckbox = document.getElementById('clusterMeteorites');
        const massRangeMinInput = document.getElementById('massRangeMin');
        const massRangeMaxInput = document.getElementById('massRangeMax');
        const massRangeValue = document.getElementById('massRangeValue');
        const yearRangeMinInput = document.getElementById('yearRangeMin');
        const yearRangeMaxInput = document.getElementById('yearRangeMax');
        const yearRangeValue = document.getElementById('yearRangeValue');
        const diameterRangeMinInput = document.getElementById('diameterRangeMin');
        const diameterRangeMaxInput = document.getElementById('diameterRangeMax');
        const diameterRangeValue = document.getElementById('diameterRangeValue');
        const ageRangeMinInput = document.getElementById('ageRangeMin');
        const ageRangeMaxInput = document.getElementById('ageRangeMax');
        const ageRangeValue = document.getElementById('ageRangeValue');
        const targetRockSelect = document.getElementById('targetRockSelect');
        const basemapSelector = document.getElementById('basemapSelector');
        const refreshButton = document.getElementById('refreshButton');
        const searchInput = document.getElementById('searchInput');
        const searchButton = document.getElementById('searchButton');
        const modal = document.getElementById('modal');
        const closeModalButton = document.getElementById('closeModal');
        const craterModal = document.getElementById('craterModal');
        const closeCraterModalButton = document.getElementById('closeCraterModal');
        const infoModal = document.getElementById('infoModal');
        const infoButton = document.getElementById('infoButton');
        const closeInfoModalButton = document.getElementById('closeInfoModal');
        const meteoriteBar = document.getElementById('meteoriteBar');
        const craterBar = document.getElementById('craterBar');

        toggleMeteoritesCheckbox.addEventListener('change', applyFilters);
        toggleCratersCheckbox.addEventListener('change', applyCraterFilters);
        clusterMeteoritesCheckbox.addEventListener('change', () => {
            applyFilters();
        });
        massRangeMinInput.addEventListener('input', () => {
            massMin = parseInt(massRangeMinInput.value);
            massRangeValue.textContent = `${massMin.toLocaleString()} g - ${massMax.toLocaleString()} g`;
            applyFilters();
        });
        massRangeMaxInput.addEventListener('input', () => {
            massMax = parseInt(massRangeMaxInput.value);
            massRangeValue.textContent = `${massMin.toLocaleString()} g - ${massMax.toLocaleString()} g`;
            applyFilters();
        });
        yearRangeMinInput.addEventListener('input', () => {
            yearMin = parseInt(yearRangeMinInput.value);
            yearRangeValue.textContent = `${yearMin} - ${yearMax}`;
            applyFilters();
        });
        yearRangeMaxInput.addEventListener('input', () => {
            yearMax = parseInt(yearRangeMaxInput.value);
            yearRangeValue.textContent = `${yearMin} - ${yearMax}`;
            applyFilters();
        });
        diameterRangeMinInput.addEventListener('input', () => {
            diameterMin = parseInt(diameterRangeMinInput.value);
            diameterRangeValue.textContent = `${diameterMin} km - ${diameterMax} km`;
            applyCraterFilters();
        });
        diameterRangeMaxInput.addEventListener('input', () => {
            diameterMax = parseInt(diameterRangeMaxInput.value);
            diameterRangeValue.textContent = `${diameterMin} km - ${diameterMax} km`;
            applyCraterFilters();
        });
        ageRangeMinInput.addEventListener('input', () => {
            ageMinValue = parseInt(ageRangeMinInput.value);
            ageRangeValue.textContent = `${ageMinValue} Ma - ${ageMaxValue} Ma`;
            applyCraterFilters();
        });
        ageRangeMaxInput.addEventListener('input', () => {
            ageMaxValue = parseInt(ageRangeMaxInput.value);
            ageRangeValue.textContent = `${ageMinValue} Ma - ${ageMaxValue} Ma`;
            applyCraterFilters();
        });
        targetRockSelect.addEventListener('change', () => {
            selectedTargetRocks = Array.from(targetRockSelect.selectedOptions).map(option => option.value);
            applyCraterFilters();
        });
        basemapSelector.addEventListener('change', updateBasemap);
        refreshButton.addEventListener('click', () => {
            massMin = 0;
            massMax = 1000000;
            massRangeMinInput.value = massMin;
            massRangeMaxInput.value = massMax;
            massRangeValue.textContent = `${massMin.toLocaleString()} g - ${massMax.toLocaleString()} g`;

            yearMin = 860;
            yearMax = 2023;
            yearRangeMinInput.value = yearMin;
            yearRangeMaxInput.value = yearMax;
            yearRangeValue.textContent = `${yearMin} - ${yearMax}`;

            diameterMin = 0;
            diameterMax = 300;
            diameterRangeMinInput.value = diameterMin;
            diameterRangeMaxInput.value = diameterMax;
            diameterRangeValue.textContent = `${diameterMin} km - ${diameterMax} km`;

            ageMinValue = 0;
            ageMaxValue = 2000;
            ageRangeMinInput.value = ageMinValue;
            ageRangeMaxInput.value = ageMaxValue;
            ageRangeValue.textContent = `${ageMinValue} Ma - ${ageMaxValue} Ma`;

            selectedTargetRocks = [];
            Array.from(targetRockSelect.options).forEach(option => option.selected = false);

            applyFilters();
            applyCraterFilters();
        });

        searchButton.addEventListener('click', () => {
            const query = searchInput.value;
            if (query) {
                viewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(0, 0, 30000000)
                });
                viewer.entities.removeAll();
                viewer.geocoder.viewModel.searchText = query;
                viewer.geocoder.viewModel.search();
            }
        });

        closeModalButton.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        closeCraterModalButton.addEventListener('click', () => {
            craterModal.style.display = 'none';
        });

        infoButton.addEventListener('click', () => {
            infoModal.style.display = 'block';
        });

        closeInfoModalButton.addEventListener('click', () => {
            infoModal.style.display = 'none';
        });

        viewer.screenSpaceEventHandler.setInputAction(function onLeftClick(movement) {
            const pickedObject = viewer.scene.pick(movement.position);
            if (pickedObject && pickedObject.id) {
                const id = pickedObject.id;
                if (id.properties) {
                    const props = id.properties;
                    alert(`Crater: ${props.name}\nDiameter: ${props.diameter_km} km\nAge: ${props.age_ma} Ma`);
                } else {
                    alert(`Meteorite: ${id.name}\nMass: ${id.mass} g\nYear: ${new Date(id.year).getFullYear()}`);
                }
            }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

        // Show/hide key menu
        const keyButton = document.getElementById('keyButton');
        const keyMenu = document.getElementById('keyMenu');
        const closeKey = document.getElementById('closeKey');

        keyButton.onclick = () => {
            if (keyMenu.style.display === 'none' || keyMenu.style.display === '') {
                keyMenu.style.display = 'block';
            } else {
                keyMenu.style.display = 'none';
            }
        };

        closeKey.onclick = () => {
            keyMenu.style.display = 'none';
        };

        // Show/hide options menu
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

        function populateTargetRockOptions() {
            const targetRocks = [...new Set(allCraters.map(crater => crater.properties.target_rock || '').filter(Boolean))];
            targetRocks.sort();

            targetRocks.forEach(rock => {
                const option = document.createElement('option');
                option.value = rock;
                option.textContent = rock;
                targetRockSelect.appendChild(option);
            });
        }

        massRangeValue.textContent = `${massMin.toLocaleString()} g - ${massMax.toLocaleString()} g`;
        yearRangeValue.textContent = `${yearMin} - ${yearMax}`;
        diameterRangeValue.textContent = `${diameterMin} km - ${diameterMax} km`;
        ageRangeValue.textContent = `${ageMinValue} Ma - ${ageMaxValue} Ma`;

        populateTargetRockOptions();
        fetchAllMeteorites();
        applyCraterFilters();
        updateBasemap();

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
