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
            transition: padding 0.3s;
        }
        #header h1 {
            margin: 0;
            font-size: 20px;
            color: #333;
            text-align: center;
        }
        #infoIcon {
            margin-top: 5px;
            cursor: pointer;
            font-size: 18px;
            color: #0078D7;
        }
        #controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            align-items: center;
            margin-top: 10px;
        }
        #controls label {
            font-size: 14px;
            color: #333;
        }
        #yearRangeContainer, #massRangeContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        #yearRange, #massRange {
            width: 150px;
        }
        #controls button, #controls select {
            padding: 6px 12px;
            font-size: 14px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background-color: #0078D7;
            color: #fff;
            transition: background-color 0.3s;
        }
        #controls button:hover, #controls select:hover {
            background-color: #005a9e;
        }
        /* Toggle Buttons */
        #toggleButtons {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }
        #toggleButtons label {
            font-size: 14px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
        }
        /* Legend Styling */
        #legend {
            margin-top: 15px;
            background: rgba(255,255,255,0.9);
            padding: 10px 15px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }
        .legend-section {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-color, .legend-size {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .legend-icon img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
        }
        .legend-size {
            background-color: red;
        }
        /* Meteorite Bar Styling */
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
        #topBar::-webkit-scrollbar {
            height: 8px;
        }
        #topBar::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 4px;
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
        /* Modal Styling */
        #modal, #infoModal {
            display: none;
            position: fixed;
            z-index: 4;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.5);
        }
        #modalContent, #infoContent {
            background-color: #fff;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 90%;
            max-width: 800px;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        #closeModal, #closeInfo {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        #closeModal:hover, #closeModal:focus,
        #closeInfo:hover, #closeInfo:focus {
            color: #000;
            text-decoration: none;
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
        /* Search Box Styling */
        #searchBox {
            position: absolute;
            top: 10px;
            right: 20px;
            z-index: 4;
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.95);
            padding: 5px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        #searchInput {
            border: none;
            outline: none;
            padding: 5px;
            font-size: 14px;
        }
        #searchButton {
            border: none;
            background: none;
            cursor: pointer;
            font-size: 16px;
            padding: 5px;
        }
        /* Total Meteorites Count Styling */
        #totalItems {
            margin-top: 10px;
            font-size: 16px;
            color: #333;
        }
        /* Responsive Design */
        @media (max-width: 768px) {
            #header {
                padding: 8px 15px;
            }
            #header h1 {
                font-size: 18px;
            }
            #controls {
                flex-direction: column;
                gap: 8px;
            }
            #legend {
                flex-direction: column;
                gap: 8px;
            }
            #topBar {
                padding: 8px 0;
            }
            .bar-item {
                margin: 0 10px;
                font-size: 12px;
            }
            #searchBox {
                top: 8px;
                right: 15px;
            }
            #totalItems {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>

    <!-- Header with title, info icon, and controls -->
    <div id="header">
        <div style="display: flex; align-items: center; gap: 10px;">
            <h1>🌠 Meteorite & Crater Visualization</h1>
            <span id="infoIcon">ℹ️</span>
        </div>
        <div id="controls">
            <div id="yearRangeContainer">
                <label for="yearRange">Year Range: <span id="yearRangeValue">860 - 2023</span></label>
                <input type="range" id="yearRangeMin" min="860" max="2023" value="860" step="1">
                <input type="range" id="yearRangeMax" min="860" max="2023" value="2023" step="1">
            </div>
            <div id="massRangeContainer">
                <label for="massRange">Mass Range (g): <span id="massRangeValue">0g - 60000g</span></label>
                <input type="range" id="massRangeMin" min="0" max="60000" value="0" step="1000">
                <input type="range" id="massRangeMax" min="0" max="60000" value="60000" step="1000">
            </div>
            <select id="basemapSelector">
                <option value="Cesium World Imagery">Cesium World Imagery (Default)</option>
                <option value="OpenStreetMap">OpenStreetMap</option>
            </select>
        </div>
        <div id="toggleButtons">
            <label>
                <input type="radio" name="viewToggle" id="toggleMeteorites" value="meteorites" checked>
                Show Meteorites
            </label>
            <label>
                <input type="radio" name="viewToggle" id="toggleCraters" value="craters">
                Show Impact Craters
            </label>
        </div>
        <div id="totalItems">Total Meteorites: 0</div>
        <div id="legend">
            <div id="meteoriteLegend" class="legend-section">
                <div class="legend-color" style="background-color: cyan;"></div>
                <span>Mass &lt; 1,000g</span>
                <div class="legend-color" style="background-color: green;"></div>
                <span>1,000g ≤ Mass &lt; 10,000g</span>
                <div class="legend-color" style="background-color: yellow;"></div>
                <span>10,000g ≤ Mass &lt; 50,000g</span>
                <div class="legend-color" style="background-color: orange;"></div>
                <span>50,000g ≤ Mass &lt; 100,000g</span>
                <div class="legend-color" style="background-color: red;"></div>
                <span>Mass ≥ 100,000g</span>
            </div>
            <div id="craterLegend" class="legend-section" style="display: none;">
                <div class="legend-size" style="width: 5px; height: 5px;"></div>
                <span>Crater Diameter: &lt; 10 km</span>
                <div class="legend-size" style="width: 10px; height: 10px;"></div>
                <span>Crater Diameter: 10-30 km</span>
                <div class="legend-size" style="width: 15px; height: 15px;"></div>
                <span>Crater Diameter: 30-50 km</span>
                <div class="legend-size" style="width: 20px; height: 20px;"></div>
                <span>Crater Diameter: ≥ 50 km</span>
                <div class="legend-icon">
                    <img src="https://cdn-icons-png.flaticon.com/512/684/684908.png" alt="Impact Crater">
                </div>
                <span>Impact Crater</span>
            </div>
        </div>
    </div>

    <!-- Top bar for Meteorites or Craters -->
    <div id="topBar">
        <!-- Populated dynamically -->
    </div>

    <!-- Search box -->
    <div id="searchBox">
        <input type="text" id="searchInput" placeholder="Search location...">
        <button id="searchButton">🔍</button>
    </div>

    <!-- Tooltip -->
    <div id="tooltip"></div>

    <!-- Modal for viewing all Meteorites or Craters -->
    <div id="modal">
        <div id="modalContent">
            <span id="closeModal">&times;</span>
            <h2 id="modalTitle">All Meteorites</h2>
            <table id="fullItemTable">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Mass/Diameter</th>
                        <th>Class/Target Rock</th>
                        <th>Year/Age</th>
                        <th>Fall/Find/Exposed</th>
                        <th>Info</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <!-- Info Modal -->
    <div id="infoModal">
        <div id="infoContent">
            <span id="closeInfo">&times;</span>
            <h2>About This Visualization</h2>
            <p>
                This application visualizes global meteorite landing sites and Earth's impact craters in an interactive 3D map using CesiumJS.
                Use the controls above to filter data based on year and mass, toggle between viewing meteorites and impact craters, and explore detailed information by interacting with the markers or the top lists.
            </p>
        </div>
    </div>

    <!-- Script Section -->
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
        let allCraters = impactCraters.features || [];
        let filteredCraters = [];

        // Data Sources for Meteorites and Craters
        let meteoriteEntities = new Cesium.CustomDataSource('meteorites');
        viewer.dataSources.add(meteoriteEntities);

        let craterEntities = new Cesium.CustomDataSource('craters');
        viewer.dataSources.add(craterEntities);

        let currentView = 'meteorites'; // 'meteorites' or 'craters'

        // Function to get color based on mass
        function getMeteoriteColor(mass) {
            if (mass >= 100000) return Cesium.Color.RED.withAlpha(0.6);
            if (mass >= 50000)  return Cesium.Color.ORANGE.withAlpha(0.6);
            if (mass >= 10000)  return Cesium.Color.YELLOW.withAlpha(0.6);
            if (mass >= 1000)   return Cesium.Color.GREEN.withAlpha(0.6);
            return Cesium.Color.CYAN.withAlpha(0.6);
        }

        // Function to get size based on crater diameter
        function getCraterSize(diameter) {
            if (diameter >= 50) return 20;
            if (diameter >= 30) return 15;
            if (diameter >= 10) return 10;
            return 5;
        }

        // Fetch all meteorites from NASA API
        function fetchAllMeteorites() {
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

        // Apply filters and update the map
        function applyFilters() {
            let yearMin = parseInt(document.getElementById('yearRangeMin').value);
            let yearMax = parseInt(document.getElementById('yearRangeMax').value);
            let massMin = parseInt(document.getElementById('massRangeMin').value);
            let massMax = parseInt(document.getElementById('massRangeMax').value);

            // Ensure min is not greater than max
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

            if (currentView === 'meteorites') {
                filteredMeteorites = allMeteorites.filter(m => {
                    const year = m.year ? new Date(m.year).getFullYear() : null;
                    const mass = m.mass ? parseFloat(m.mass) : null;

                    const yearMatch = year ? (year >= yearMin && year <= yearMax) : true;
                    const massMatch = mass ? (mass >= massMin && mass <= massMax) : true;

                    return yearMatch && massMatch;
                });
                updateMeteoriteData();
                updateTopBar();
                updateTotalCount();
                updateModalTable();
            } else if (currentView === 'craters') {
                filteredCraters = allCraters.filter(c => {
                    const age = c.properties.age_millions_years_ago ? parseFloat(c.properties.age_millions_years_ago.replace(/[^0-9.]/g, '')) : null;
                    const diameter = c.properties.diameter_km ? parseFloat(c.properties.diameter_km) : null;

                    const diameterMatch = diameter ? (diameter >= massMin && diameter <= massMax) : true;
                    // Assuming 'massMin' and 'massMax' are repurposed for diameter filtering in crater mode

                    return diameterMatch;
                });
                updateCraterData();
                updateTopBar();
                updateTotalCount();
                updateModalTable();
            }
        }

        // Update total items count
        function updateTotalCount() {
            if (currentView === 'meteorites') {
                document.getElementById('totalItems').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
            } else if (currentView === 'craters') {
                document.getElementById('totalItems').innerText = `Total Impact Craters: ${filteredCraters.length}`;
            }
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
                    const id = meteorite.id || 'Unknown';
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                    const massDisplay = formatMass(mass);
                    const recclass = meteorite.recclass || 'Unknown';
                    const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                    const fall = meteorite.fall || 'Unknown';

                    meteoriteEntities.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 1000, 5), 25) : 5,
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

        // Update impact crater data on the map
        function updateCraterData() {
            craterEntities.entities.removeAll();

            filteredCraters.forEach((feature, index) => {
                const properties = feature.properties;
                const geometry = feature.geometry;

                if (geometry && geometry.type === "Point") {
                    const [lon, lat] = geometry.coordinates;
                    const name = properties.crater_name || 'Unknown';
                    const age = properties.age_millions_years_ago || 'Unknown';
                    const diameter = properties.diameter_km ? parseFloat(properties.diameter_km) : 1;
                    const country = properties.country || 'Unknown';
                    const target_rock = properties.target_rock || 'Unknown';
                    const url = properties.url || '#';

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

        // Format mass or diameter value for display
        function formatMass(value) {
            if (value === 'Unknown' || isNaN(value)) return 'Unknown';
            if (currentView === 'meteorites') {
                if (value > 500) {
                    return (value / 1000).toFixed(2) + ' kg';
                } else {
                    return value + ' g';
                }
            } else if (currentView === 'craters') {
                return value + ' km';
            }
        }

        // Update the top bar based on current view
        function updateTopBar() {
            const bar = document.getElementById('topBar');
            bar.innerHTML = '';

            if (currentView === 'meteorites') {
                const sortedMeteorites = filteredMeteorites.filter(m => m.mass).sort((a, b) => parseFloat(b.mass) - parseFloat(a.mass));
                const top10 = sortedMeteorites.slice(0, 10);
                bar.innerHTML = '<div class="bar-item"><strong>Top Meteorites:</strong></div>';

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

                const viewAll = document.createElement('div');
                viewAll.className = 'bar-item';
                viewAll.innerHTML = `<strong>View All</strong>`;
                viewAll.onclick = () => openModal();
                bar.appendChild(viewAll);
            } else if (currentView === 'craters') {
                const sortedCraters = filteredCraters.filter(c => c.properties.diameter_km).sort((a, b) => parseFloat(b.properties.diameter_km) - parseFloat(a.properties.diameter_km));
                const top10 = sortedCraters.slice(0, 10);
                bar.innerHTML = '<div class="bar-item"><strong>Top Impact Craters:</strong></div>';

                top10.forEach((crater, index) => {
                    const originalIndex = filteredCraters.indexOf(crater);
                    const name = crater.properties.crater_name || 'Unknown';
                    const diameter = parseFloat(crater.properties.diameter_km) || 0;
                    const diameterDisplay = formatMass(diameter);
                    const div = document.createElement('div');
                    div.className = 'bar-item';
                    div.innerText = `🔺 ${name} - ${diameterDisplay}`;
                    div.onclick = () => flyToCrater(originalIndex);
                    bar.appendChild(div);
                });

                const viewAll = document.createElement('div');
                viewAll.className = 'bar-item';
                viewAll.innerHTML = `<strong>View All</strong>`;
                viewAll.onclick = () => openModal();
                bar.appendChild(viewAll);
            }
        }

        // Fly to a specific meteorite location
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
                    destination: Cesium.Cartesian3.fromDegrees(lon, lat, 200000),
                    duration: 2,
                    orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(-30) }
                });
            }
        }

        // Fly to a specific crater location
        function flyToCrater(index) {
            const crater = filteredCraters[index];
            if (!crater) {
                console.error('Invalid crater index:', index);
                return;
            }
            const [lon, lat] = crater.geometry.coordinates;

            if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
                viewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(lon, lat, 300000),
                    duration: 2,
                    orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(-30) }
                });
            }
        }

        // Tooltip functionality
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

        // Update tooltip position based on mouse movement
        function updateTooltipPosition(position) {
            const x = position.x + 15;
            const y = position.y + 15;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        // Modal functionality for viewing all items
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const fullItemTable = document.getElementById('fullItemTable').getElementsByTagName('tbody')[0];
        document.getElementById('closeModal').onclick = () => modal.style.display = 'none';

        // Open modal to display all items
        function openModal() {
            if (currentView === 'meteorites') {
                modalTitle.innerText = 'All Meteorites';
                populateMeteoriteTable();
            } else if (currentView === 'craters') {
                modalTitle.innerText = 'All Impact Craters';
                populateCraterTable();
            }
            modal.style.display = 'block';
        }

        // Populate Meteorite table
        function populateMeteoriteTable() {
            if (!filteredMeteorites.length) {
                fullItemTable.innerHTML = '<tr><td colspan="6">No meteorite data available.</td></tr>';
                return;
            }
            fullItemTable.innerHTML = filteredMeteorites.map((meteorite, index) => {
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
                        <td></td>
                    </tr>
                `;
            }).join('');
        }

        // Populate Crater table
        function populateCraterTable() {
            if (!filteredCraters.length) {
                fullItemTable.innerHTML = '<tr><td colspan="6">No impact crater data available.</td></tr>';
                return;
            }
            fullItemTable.innerHTML = filteredCraters.map((crater, index) => {
                const name = crater.properties.crater_name || 'Unknown';
                const diameter = parseFloat(crater.properties.diameter_km) || 'Unknown';
                const diameterDisplay = formatMass(diameter);
                const target_rock = crater.properties.target_rock || 'Unknown';
                const age = crater.properties.age_millions_years_ago || 'Unknown';
                const exposed = crater.properties.exposed ? 'Yes' : 'No';
                const url = crater.properties.url || '#';
                return `
                    <tr onclick='flyToCrater(${index})' style="cursor:pointer;">
                        <td>${name}</td>
                        <td>${diameterDisplay}</td>
                        <td>${target_rock}</td>
                        <td>${age}</td>
                        <td>${exposed}</td>
                        <td><a href="${url}" target="_blank">🔗</a></td>
                    </tr>
                `;
            }).join('');
        }

        // Ensure flyTo functions are accessible globally
        window.flyToMeteorite = flyToMeteorite;
        window.flyToCrater = flyToCrater;

        // Search location functionality
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
                            orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(-30) }
                        });
                    } else {
                        alert('Location not found.');
                    }
                })
                .catch(error => {
                    console.error('Error searching location:', error);
                });
        }

        // Basemap selector functionality
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

        // Initialize the basemap selector to default
        document.getElementById('basemapSelector').value = 'Cesium World Imagery';

        // Event listeners for filters
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

        // Toggle buttons for meteorites and craters
        const toggleMeteorites = document.getElementById('toggleMeteorites');
        const toggleCraters = document.getElementById('toggleCraters');

        toggleMeteorites.addEventListener('change', function() {
            if (this.checked) {
                currentView = 'meteorites';
                craterEntities.show = false;
                meteoriteEntities.show = true;
                document.getElementById('meteoriteLegend').style.display = 'flex';
                document.getElementById('craterLegend').style.display = 'none';
                updateTopBar();
                updateTotalCount();
            }
        });

        toggleCraters.addEventListener('change', function() {
            if (this.checked) {
                currentView = 'craters';
                meteoriteEntities.show = false;
                craterEntities.show = true;
                document.getElementById('meteoriteLegend').style.display = 'none';
                document.getElementById('craterLegend').style.display = 'flex';
                updateTopBar();
                updateTotalCount();
            }
        });

        // Initialize sliders display
        function initializeSliders() {
            updateSlidersDisplay();
        }

        // Update sliders display
        function updateSlidersDisplay() {
            const yearMin = parseInt(document.getElementById('yearRangeMin').value);
            const yearMax = parseInt(document.getElementById('yearRangeMax').value);
            document.getElementById('yearRangeValue').innerText = `${yearMin} - ${yearMax}`;

            const massMin = parseInt(document.getElementById('massRangeMin').value);
            const massMax = parseInt(document.getElementById('massRangeMax').value);
            document.getElementById('massRangeValue').innerText = `${formatMass(massMin)} - ${formatMass(massMax)}`;
        }

        // Initialize sliders display on page load
        initializeSliders();

        // Fetch all meteorite data on page load
        fetchAllMeteorites();

        // Update tractable on initial load
        updateTopBar();

        // Toggle for info modal
        const infoModal = document.getElementById('infoModal');
        const infoIcon = document.getElementById('infoIcon');
        const closeInfo = document.getElementById('closeInfo');

        infoIcon.onclick = () => {
            infoModal.style.display = 'block';
        };
        closeInfo.onclick = () => {
            infoModal.style.display = 'none';
        };
        window.onclick = event => { 
            if (event.target == modal) modal.style.display = 'none'; 
            if (event.target == infoModal) infoModal.style.display = 'none';
        };

        // Ensure flyTo functions are accessible globally
        window.flyToMeteorite = flyToMeteorite;
        window.flyToCrater = flyToCrater;

        // Add impact craters to the map initially (if meteorites are shown by default)
        // No action needed here since 'meteorites' are shown initially
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
