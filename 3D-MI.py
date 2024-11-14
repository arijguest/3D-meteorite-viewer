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
            padding: 15px 30px;
            box-sizing: border-box;
            z-index: 3;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #header h1 {
            margin: 0;
            font-size: 24px;
            color: #333;
            text-align: center;
        }
        #header p {
            margin: 8px 0 15px 0;
            font-size: 14px;
            color: #666;
            text-align: center;
            max-width: 800px;
        }
        #controls {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
            align-items: center;
            position: relative;
            width: 100%;
        }
        #controls label {
            font-size: 14px;
            color: #333;
        }
        #yearRangeContainer, #massRangeContainer, #diameterRangeContainer, #ageRangeContainer, #targetRockContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        #yearRange, #massRange, #diameterRange, #ageRange {
            width: 200px;
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
        /* Information Button Styling */
        #infoButton {
            background: #0078D7;
            color: #fff;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
            margin-left: 10px;
        }
        #infoButton:hover {
            background-color: #005a9e;
        }
        /* Toggle Buttons */
        #toggleButtons {
            display: flex;
            gap: 10px;
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
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
            width: 90%;
            max-width: 600px;
        }
        .legend-section {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-color, .legend-icon, .legend-size {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .legend-color {
            border-radius: 4px;
        }
        .legend-icon img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
        }
        .legend-size {
            border-radius: 50%;
        }
        /* Meteorite Bar Styling */
        #meteoriteBar {
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
        #meteoriteBar::-webkit-scrollbar {
            height: 8px;
        }
        #meteoriteBar::-webkit-scrollbar-thumb {
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
        #modalContent, #infoModalContent {
            background-color: #fff;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 90%;
            max-width: 800px;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        #closeModal, #closeInfoModal {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        #closeModal:hover,
        #closeModal:focus,
        #closeInfoModal:hover,
        #closeInfoModal:focus {
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
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.95);
            padding: 5px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-top: 15px;
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
        /* Information Button Positioning */
        #infoButton {
            position: absolute;
            top: 15px;
            left: 30px;
            z-index: 4;
        }
        /* Total Counts Styling */
        #totals {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }
        #totalMeteorites, #totalCraters {
            font-size: 16px;
            color: #333;
        }
        /* Responsive Design */
        @media (max-width: 768px) {
            #header {
                padding: 10px 20px;
            }
            #header h1 {
                font-size: 20px;
            }
            #header p {
                font-size: 12px;
            }
            #controls {
                flex-direction: column;
                gap: 10px;
            }
            #legend {
                flex-direction: column;
                gap: 8px;
            }
            #meteoriteBar {
                padding: 8px 0;
            }
            .bar-item {
                margin: 0 10px;
                font-size: 12px;
            }
            #searchBox {
                margin-top: 10px;
            }
            #totals {
                flex-direction: column;
                align-items: center;
                gap: 5px;
            }
            #totalMeteorites, #totalCraters {
                font-size: 14px;
            }
            #infoButton {
                top: 10px;
                left: 20px;
            }
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>

    <!-- Header with title, description, controls, toggles, total counts, and search bar -->
    <div id="header">
        <h1>🌠 Global Meteorite Impacts and Earth Craters Visualization</h1>
        <p>Explore meteorite landing sites and impact craters around the world in an interactive 3D map.</p>
        <div id="controls">
            <div id="yearRangeContainer">
                <label for="yearRangeMin">Year Range: <span id="yearRangeValue">860 - 2023</span></label>
                <input type="range" id="yearRangeMin" min="860" max="2023" value="860" step="1">
                <input type="range" id="yearRangeMax" min="860" max="2023" value="2023" step="1">
            </div>
            <div id="massRangeContainer">
                <label for="massRangeMin">Mass Range (g): <span id="massRangeValue">0g - 60000g</span></label>
                <input type="range" id="massRangeMin" min="0" max="60000" value="0" step="1000">
                <input type="range" id="massRangeMax" min="0" max="60000" value="60000" step="1000">
            </div>
            <!-- New Crater Filters -->
            <div id="diameterRangeContainer">
                <label for="diameterRangeMin">Crater Diameter (km): <span id="diameterRangeValue">0 - 300</span></label>
                <input type="range" id="diameterRangeMin" min="0" max="300" value="0" step="1">
                <input type="range" id="diameterRangeMax" min="0" max="300" value="300" step="1">
            </div>
            <div id="ageRangeContainer">
                <label for="ageRangeMin">Crater Age (Myr): <span id="ageRangeValue">0 - 2000</span></label>
                <input type="range" id="ageRangeMin" min="0" max="2000" value="0" step="10">
                <input type="range" id="ageRangeMax" min="0" max="2000" value="2000" step="10">
            </div>
            <div id="targetRockContainer">
                <label for="targetRockSelect">Target Rock:</label>
                <select id="targetRockSelect" multiple>
                    <!-- Options populated dynamically -->
                </select>
            </div>
            <select id="basemapSelector">
                <option value="Cesium World Imagery">Cesium World Imagery (Default)</option>
                <option value="OpenStreetMap">OpenStreetMap</option>
            </select>
        </div>
        <button id="refreshButton">Refresh Options</button>
        <div id="toggleButtons">
            <label>
                <input type="checkbox" id="toggleMeteorites" checked>
                Show Meteorites
            </label>
            <label>
                <input type="checkbox" id="toggleCraters" checked>
                Show Impact Craters
            </label>
        </div>
        <div id="totals">
            <div id="totalMeteorites">Total Meteorites: 0</div>
            <div id="totalCraters">Total Impact Craters: 0</div>
        </div>
        <div id="legend">
            <div class="legend-section">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: cyan;"></div>
                    <span>&lt; 1 kg</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: green;"></div>
                    <span>1 kg - 10 kg</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: yellow;"></div>
                    <span>10 kg - 50 kg</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: orange;"></div>
                    <span>50 kg - 100 kg</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: red;"></div>
                    <span>&ge; 100 kg</span>
                </div>
            </div>
            <div class="legend-section">
                <div class="legend-item">
                    <div class="legend-size" style="background-color: lightblue; width:10px; height:10px;"></div>
                    <span>&lt; 10 km</span>
                </div>
                <div class="legend-item">
                    <div class="legend-size" style="background-color: blue; width:15px; height:15px;"></div>
                    <span>10 km - 30 km</span>
                </div>
                <div class="legend-item">
                    <div class="legend-size" style="background-color: darkblue; width:20px; height:20px;"></div>
                    <span>30 km - 50 km</span>
                </div>
                <div class="legend-item">
                    <div class="legend-size" style="background-color: navy; width:25px; height:25px;"></div>
                    <span>&ge; 50 km</span>
                </div>
            </div>
        </div>
        <div id="searchBox">
            <input type="text" id="searchInput" placeholder="Search location...">
            <button id="searchButton">🔍</button>
        </div>
    </div>

    <!-- Information Button placed next to the map view -->
    <button id="infoButton">Information</button>

    <!-- Top meteorites bar -->
    <div id="meteoriteBar">
        <!-- Populated dynamically -->
    </div>

    <!-- Tooltip -->
    <div id="tooltip"></div>

    <!-- Modal for viewing all meteorites -->
    <div id="modal">
        <div id="modalContent">
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

    <!-- Modal for information -->
    <div id="infoModal">
        <div id="infoModalContent">
            <span id="closeInfoModal">&times;</span>
            <h2>Information</h2>
            <p><strong>About the Program:</strong> This application visualizes meteorite landing sites and impact craters around the world in an interactive 3D map using CesiumJS.</p>
            <p><strong>Data Sources:</strong></p>
            <ul>
                <li><strong>Meteorite Data:</strong> NASA Open Data API.</li>
                <li><strong>Impact Crater Data:</strong> earth-impact-craters.geojson file.</li>
            </ul>
            <p><strong>Key Terminology:</strong></p>
            <ul>
                <li><strong>Mass:</strong> The mass of the meteorite in grams or kilograms.</li>
                <li><strong>Crater Diameter:</strong> The diameter of the impact crater in kilometers.</li>
                <li><strong>Crater Age:</strong> The age of the crater in million years ago.</li>
            </ul>
            <p><strong>Fun Facts:</strong></p>
            <ul>
                <li>The largest meteorite ever found on Earth is the Hoba Meteorite in Namibia, weighing approximately 60 tons.</li>
                <li>Impact craters can provide valuable information about Earth's geological history.</li>
                <li>Meteorites can be classified into different types based on their composition, such as stony, iron, and stony-iron.</li>
            </ul>
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
        let filteredCraters = [];
        const allCraters = impactCraters.features;

        // Data Sources for Meteorites and Craters
        let meteoriteEntities = new Cesium.CustomDataSource('meteorites');
        viewer.dataSources.add(meteoriteEntities);

        let craterEntities = new Cesium.CustomDataSource('craters');
        viewer.dataSources.add(craterEntities);

        // Function to get color based on mass
        function getMeteoriteColor(mass) {
            if (mass >= 100000) return Cesium.Color.RED.withAlpha(0.6);
            if (mass >= 50000)  return Cesium.Color.ORANGE.withAlpha(0.6);
            if (mass >= 10000)  return Cesium.Color.YELLOW.withAlpha(0.6);
            if (mass >= 1000)   return Cesium.Color.GREEN.withAlpha(0.6);
            return Cesium.Color.CYAN.withAlpha(0.6);
        }

        // Function to get color based on crater diameter
        function getCraterColor(diameter) {
            if (diameter >= 50) return Cesium.Color.NAVY.withAlpha(0.8);
            if (diameter >= 30) return Cesium.Color.DARKBLUE.withAlpha(0.8);
            if (diameter >= 10) return Cesium.Color.BLUE.withAlpha(0.8);
            return Cesium.Color.LIGHTBLUE.withAlpha(0.8);
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
            // Meteorite Filters
            let yearMin = parseInt(document.getElementById('yearRangeMin').value);
            let yearMax = parseInt(document.getElementById('yearRangeMax').value);
            let massMin = parseInt(document.getElementById('massRangeMin').value);
            let massMax = parseInt(document.getElementById('massRangeMax').value);

            // Crater Filters
            let diameterMin = parseInt(document.getElementById('diameterRangeMin').value);
            let diameterMax = parseInt(document.getElementById('diameterRangeMax').value);
            let ageMin = parseInt(document.getElementById('ageRangeMin').value);
            let ageMax = parseInt(document.getElementById('ageRangeMax').value);
            const selectedRocks = Array.from(document.getElementById('targetRockSelect').selectedOptions).map(option => option.value);

            // Ensure min is not greater than max for meteorites
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

            // Ensure min is not greater than max for craters
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

            // Filter Meteorites
            filteredMeteorites = allMeteorites.filter(m => {
                const year = m.year ? new Date(m.year).getFullYear() : null;
                const mass = m.mass ? parseFloat(m.mass) : null;

                const yearMatch = year ? (year >= yearMin && year <= yearMax) : true;
                const massMatch = mass ? (mass >= massMin && mass <= massMax) : true;

                return yearMatch && massMatch;
            });

            // Filter Craters
            filteredCraters = allCraters.filter(feature => {
                const properties = feature.properties;
                let diameter = parseFloat(properties.diameter_km) || 0;
                let age = properties.age_millions_years_ago || '';
                const targetRock = properties.target_rock || 'Unknown';

                const diameterMatch = diameter >= diameterMin && diameter <= diameterMax;
                const ageMatch = age !== '' ? true : false; // Assuming age must be present
                const rockMatch = selectedRocks.length ? selectedRocks.includes(targetRock) : true;

                return diameterMatch && ageMatch && rockMatch;
            });

            updateMeteoriteData();
            updateCraterData();
            updateTopMeteorites();
            updateTotalCounts();
            updateModalTable();
        }

        // Update total counts
        function updateTotalCounts() {
            document.getElementById('totalMeteorites').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
            document.getElementById('totalCraters').innerText = `Total Impact Craters: ${filteredCraters.length}`;
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
                            <b>Name:</b> <a href="${url}" target="_blank">${name}</a><br>
                            <b>Age:</b> ${age}<br>
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

        // Format mass value for display
        function formatMass(mass) {
            if (mass === 'Unknown' || isNaN(mass)) return 'Unknown';
            if (mass > 500) {
                return (mass / 1000).toFixed(2) + ' kg';
            } else {
                return mass + ' g';
            }
        }

        // Function to determine crater size based on diameter
        function getCraterSize(diameter) {
            if (diameter >= 50) return 25;
            if (diameter >= 30) return 20;
            if (diameter >= 10) return 15;
            return 10;
        }

        // Update the top meteorites list
        function updateTopMeteorites() {
            const sortedMeteorites = filteredMeteorites.filter(m => m.mass).sort((a, b) => parseFloat(b.mass) - parseFloat(a.mass));
            const top10 = sortedMeteorites.slice(0, 10);
            const bar = document.getElementById('meteoriteBar');
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
                    destination: Cesium.Cartesian3.fromDegrees(lon, lat, 1000000),
                    duration: 2,
                    orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(270) }
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

        // Modal functionality for viewing all meteorites
        const modal = document.getElementById('modal');
        document.getElementById('closeModal').onclick = () => modal.style.display = 'none';
        window.onclick = event => { if (event.target == modal) modal.style.display = 'none'; }

        // Open modal to display all meteorites
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

        // Ensure flyToMeteorite is accessible globally
        window.flyToMeteorite = flyToMeteorite;

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

        // Event listeners for meteorite filters
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

        // Event listeners for crater filters
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

        // Toggle buttons for meteorites and craters
        document.getElementById('toggleMeteorites').addEventListener('change', function() {
            meteoriteEntities.show = this.checked;
        });

        document.getElementById('toggleCraters').addEventListener('change', function() {
            craterEntities.show = this.checked;
        });

        // Refresh button functionality to reset all filters
        document.getElementById('refreshButton').onclick = resetFilters;

        function resetFilters() {
            // Reset meteorite sliders
            document.getElementById('yearRangeMin').value = 860;
            document.getElementById('yearRangeMax').value = 2023;
            document.getElementById('massRangeMin').value = 0;
            document.getElementById('massRangeMax').value = 60000;

            // Reset crater sliders
            document.getElementById('diameterRangeMin').value = 0;
            document.getElementById('diameterRangeMax').value = 300;
            document.getElementById('ageRangeMin').value = 0;
            document.getElementById('ageRangeMax').value = 2000;

            // Reset target rock selection
            const targetRockSelect = document.getElementById('targetRockSelect');
            for (let i = 0; i < targetRockSelect.options.length; i++) {
                targetRockSelect.options[i].selected = false;
            }

            // Apply filters after reset
            applyFilters();

            // Update slider display values
            updateSlidersDisplay();
            updateCraterSlidersDisplay();
        }

        // Initialize sliders display for meteorites
        function updateSlidersDisplay() {
            const yearMin = parseInt(document.getElementById('yearRangeMin').value);
            const yearMax = parseInt(document.getElementById('yearRangeMax').value);
            document.getElementById('yearRangeValue').innerText = `${yearMin} - ${yearMax}`;

            const massMin = parseInt(document.getElementById('massRangeMin').value);
            const massMax = parseInt(document.getElementById('massRangeMax').value);
            document.getElementById('massRangeValue').innerText = `${formatMass(massMin)} - ${formatMass(massMax)}`;
        }

        // Update sliders display for craters
        function updateCraterSlidersDisplay() {
            const diameterMin = parseInt(document.getElementById('diameterRangeMin').value);
            const diameterMax = parseInt(document.getElementById('diameterRangeMax').value);
            document.getElementById('diameterRangeValue').innerText = `${diameterMin} - ${diameterMax}`;

            const ageMin = parseInt(document.getElementById('ageRangeMin').value);
            const ageMax = parseInt(document.getElementById('ageRangeMax').value);
            document.getElementById('ageRangeValue').innerText = `${ageMin} - ${ageMax}`;
        }

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

        // Update modal table
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

        // Initialize crater filters
        function initializeCraterFilters() {
            populateTargetRockOptions();
        }

        // Initialize sliders and filters on page load
        function initializeSliders() {
            updateSlidersDisplay();
            updateCraterSlidersDisplay();
        }

        // Initialize sliders and filters
        initializeSliders();
        initializeCraterFilters();

        // Fetch all meteorite data on page load
        fetchAllMeteorites();

        // Information Modal Functionality
        const infoModal = document.getElementById('infoModal');
        const infoButton = document.getElementById('infoButton');
        const closeInfoModal = document.getElementById('closeInfoModal');

        infoButton.onclick = () => {
            infoModal.style.display = 'block';
        };

        closeInfoModal.onclick = () => {
            infoModal.style.display = 'none';
        };

        window.onclick = event => {
            if (event.target == modal) modal.style.display = 'none';
            if (event.target == infoModal) infoModal.style.display = 'none';
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
    # Use the port provided by the environment or default to 8080
    port = int(os.environ.get('PORT', 8080))
    # Bind to all network interfaces and use the specified port
    app.run(debug=False, host='0.0.0.0', port=port)
