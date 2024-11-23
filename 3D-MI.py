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
        #controls, #keyMenu {
            position: absolute;
            top: 100px;
            left: 10px;
            background: rgba(0, 0, 0, 0.9);
            padding: 10px;
            z-index: 1000;
            color: white;
            border-radius: 5px;
            max-height: calc(100% - 120px);
            overflow-y: auto;
            display: none;
            width: 300px;
        }
        #controls header, #keyMenu header {
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        #controls h2, #keyMenu h2 {
            margin: 0;
            padding-right: 30px;
        }
        #controls .close-button, #keyMenu .close-button {
            position: absolute;
            top: 10px;
            right: 10px;
            background: transparent;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
        }
        #controls, #keyMenu {
            padding-bottom: 20px;
            bottom: 20px;
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
            color: #FF6666; /* Light red color */
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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #closeModal, #closeInfoModal, #closeCraterModal, #controls .close-button, #keyMenu .close-button {
            color: #aaa;
            position: absolute;
            top: 10px;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        #closeModal:hover, #closeModal:focus, #closeInfoModal:hover, #closeInfoModal:focus, #closeCraterModal:hover, #closeCraterModal:focus, #controls .close-button:hover, #controls .close-button:focus, #keyMenu .close-button:hover, #keyMenu .close-button:focus {
            color: white;
            text-decoration: none;
        }
        #fullMeteoriteTable, #fullCraterTable {
            width: 100%;
            border-collapse: collapse;
            table-layout: auto;
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
        #craterTableContainer .table-wrapper {
            max-height: 60vh;
            overflow-y: auto;
        }
        /* Wrap crater table in a div to allow horizontal scrolling */
        #craterTableContainer {
            overflow-x: auto;
        }
        /* Adjust table to allow infinite width */
        #fullCraterTable {
            min-width: 100%;
        }
        /* Handle data too wide for the column gracefully */
        #fullCraterTable td {
            max-width: 200px;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        .legend-section {
            margin-bottom: 20px;
        }
        .legend-list {
            list-style: none;
            padding: 0;
        }
        .legend-list li {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-icon {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .modal-search {
            margin-bottom: 10px;
        }
        option[disabled] {
            color: #888;
        }
        /* Add this to your existing CSS */
        .highlighted-row {
            background-color: #ffff99;
            transition: background-color 0.5s ease;
        }
        /* Enhanced Info Modal Styling */
        #infoModal-content h2 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        #infoModal-content h3 {
            font-size: 22px;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        #infoModal-content ul {
            list-style: disc inside;
        }
        #infoModal-content li {
            margin-bottom: 10px;
            font-size: 16px;
        }
        #infoModal-content li::before {
            content: "🔹 ";
            margin-right: 5px;
        }
        #infoModal-content a {
            color: #FF6666; /* Light red color */
            text-decoration: underline;
            font-weight: bold;
        }
        #wrapper:fullscreen {
            width: 100%;
            height: 100%;
        }
        #header {
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            padding: 10px;
            z-index: 1001; /* Increased z-index to stay above Cesium */
            color: white;
            text-align: center;
            border-radius: 5px;
        }
        #cesiumContainer {
            width: 100%;
            height: 100%;
        }
        #loadingIndicator {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 2000;
            display: none;
        }

        .spinner {
            border: 12px solid #f3f3f3;
            border-top: 12px solid #3498db;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div id="loadingIndicator">
        <div class="spinner"></div>
    </div>
    <div id="wrapper">
        <div id="cesiumContainer"></div>
        <div id="header">
            <h1>🌠 Global Meteorite Specimens & Impact Craters 🌠</h1>
            <div>
                <button id="optionsButton">⚙️ Options</button>
                <button id="keyButton">🔑 Key</button>
                <button id="fullscreenButton">⛶ Fullscreen</button>
                <button id="infoButton">ℹ️ Info</button>
                <!-- Apply Button Added -->
                <button id="applyFiltersButton" style="display:none;">Apply</button>
            </div>
        </div>
        <div id="controls">
            <header>
                <h2>Options</h2>
                <button class="close-button" id="closeOptions">&times;</button>
            </header>
            <div style="margin-bottom: 10px;"></div>
            <div id="searchContainer">
                <input type="text" id="searchInput" placeholder="Search location...">
                <button id="searchButton">Search</button>
            </div>
            <hr>
            <h3>Meteorite Filters</h3>
            <div>
                <label><input type="checkbox" id="toggleMeteorites" checked> Show Meteorites</label>
            </div>
            <div>
                <label><strong>Year Range:</strong> <span id="yearRangeValue" class="editable-value" data-type="year"></span></label>
                <input type="range" id="yearRangeMin" min="860" max="2023" value="860">
                <input type="range" id="yearRangeMax" min="860" max="2023" value="2023">
            </div>
            <div>
                <label><strong>Mass Range:</strong> <span id="massRangeValue" class="editable-value" data-type="mass"></span></label>
                <input type="range" id="massRangeMin" min="0" max="60000000" value="0">
                <input type="range" id="massRangeMax" min="0" max="60000000" value="60000000">
            </div>
            <div>
                <label><strong>Meteorite Class:</strong></label>
                <select id="meteoriteClassSelect" multiple size="3"></select>
            </div>
            <div>
                <label><input type="checkbox" id="clusterMeteorites" checked> Enable Clustering</label>
            </div>
            <hr>
            <h3>Impact Crater Filters</h3>
            <div>
                <label><input type="checkbox" id="toggleCraters" checked> Show Impact Craters</label>
            </div>
            <div>
                <label><strong>Diameter Range (km):</strong> <span id="diameterRangeValue" class="editable-value" data-type="diameter"></span></label>
                <input type="range" id="diameterRangeMin" value="0">
                <input type="range" id="diameterRangeMax" value="300">
            </div>
            <div>
                <label><strong>Age Range:</strong> <span id="ageRangeValue" class="editable-value" data-type="age"></span></label>
                <input type="range" id="ageRangeMin" value="0">
                <input type="range" id="ageRangeMax" value="3000">
            </div>
            <div>
                <label><strong>Target Rock:</strong></label>
                <select id="targetRockSelect" multiple size="3"></select>
            </div>
            <div>
                <label><strong>Crater Type:</strong></label>
                <select id="craterTypeSelect" multiple size="3"></select>
            </div>
            <hr>
            <div>
                <button id="refreshButton">Reset Filters</button>
                <!-- Apply Button Visibility Managed via JS -->
            </div>
            <hr>
            <div>
                <span id="totalMeteorites">Total Meteorites: 0</span><br>
                <span id="totalCraters">Total Craters: 0</span>
            </div>
        </div>
        <div id="keyMenu">
            <header>
                <h2>Key</h2>
                <button class="close-button" id="closeKeyMenu">&times;</button>
            </header>
            <div>
                <label for="meteoriteColorScheme"><strong>Meteorite Color Scheme:</strong></label>
                <select id="meteoriteColorScheme"></select>
            </div>
            <div class="legend-section" id="meteoriteLegend"></div>
            <div>
                <label for="craterColorScheme"><strong>Crater Color Scheme:</strong></label>
                <select id="craterColorScheme"></select>
            </div>
            <div class="legend-section" id="craterLegend"></div>
            <div>
                <button id="resetColorSchemes">Reset Color Schemes</button>
            </div>
        </div>
        <div id="craterBar"></div>
        <div id="meteoriteBar"></div>
        <div id="tooltip"></div>
        <div id="modal">
            <div id="modal-content">
                <span id="closeModal">&times;</span>
                <h2>All Meteorites</h2>
                <input type="text" id="meteoriteSearchInput" class="modal-search" placeholder="Search meteorite...">
                <table id="fullMeteoriteTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable('fullMeteoriteTable', 0)">Name &#x25B2;&#x25BC;</th>
                            <th onclick="sortTable('fullMeteoriteTable', 1)">Mass &#x25B2;&#x25BC;</th>
                            <th onclick="sortTable('fullMeteoriteTable', 2)">Class &#x25B2;&#x25BC;</th>
                            <th onclick="sortTable('fullMeteoriteTable', 3)">Year &#x25B2;&#x25BC;</th>
                            <th onclick="sortTable('fullMeteoriteTable', 4)">Fall/Find &#x25B2;&#x25BC;</th>
                            <th onclick="sortTable('fullMeteoriteTable', 5)">MetBull &#x25B2;&#x25BC;</th>
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
                <input type="text" id="craterSearchInput" class="modal-search" placeholder="Search impact crater...">
                <div id="craterTableContainer">
                    <div class="table-wrapper">
                        <table id="fullCraterTable">
                            <thead>
                                <tr id="craterTableHeaders"></tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
                <p>For details on the abbreviations used in this table, please visit <a href="https://impact-craters.com/" target="_blank">impact-craters.com</a>.</p>
                <p>Data source: <a href="https://doi.org/10.1111/maps.13657" target="_blank">Kenkmann 2021 "The terrestrial impact crater record: A statistical analysis of morphologies, structures, ages, lithologies, and more"</a> via <a href="https://impact-craters.com/" target="_blank">Dr. Matthias Ebert</a>.</p>
            </div>
        </div>
        <div id="infoModal">
            <div id="infoModal-content">
                <span id="closeInfoModal">&times;</span>
                <h2>🌟 Application Features</h2>
                <!-- Existing Info Content -->
                <!-- ... [omitted for brevity] ... -->
            </div>
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

        let craterPropertyNames = [];

        if (allCraters.length > 0) {
            craterPropertyNames = Object.keys(allCraters[0].properties);

            // Reorder craterPropertyNames to ensure desired column order
            const desiredOrder = ['Name', 'Continent', 'Country', 'Age [Myr]', 'Crater diamter [km]', 'Crater type'];
            craterPropertyNames = desiredOrder.concat(craterPropertyNames.filter(item => !desiredOrder.includes(item)));
        }

        let meteoriteDataSource = new Cesium.CustomDataSource('meteorites');
        viewer.dataSources.add(meteoriteDataSource);

        let craterEntities = new Cesium.CustomDataSource('craters');
        viewer.dataSources.add(craterEntities);

        let meteoriteEntities = [];
        let craterEntitiesList = [];

        const colorSchemes = {
            'Default': {
                name: 'Default1',
                description: 'Red to Yellow Scale',
                colors: [
                    { threshold: 500000, color: Cesium.Color.RED.withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.ORANGE.withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.YELLOW.withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.LIGHTYELLOW.withAlpha(0.6) },
                    { threshold: 5000,      color: Cesium.Color.WHITE.withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 200, color: Cesium.Color.RED.withAlpha(0.8) },
                    { threshold: 100, color: Cesium.Color.ORANGE.withAlpha(0.8) },
                    { threshold: 50, color: Cesium.Color.YELLOW.withAlpha(0.8) },
                    { threshold: 10, color: Cesium.Color.LIGHTYELLOW.withAlpha(0.8) },
                    { threshold: 5, color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
                ]
            },
            /* Other color schemes */
            /* ... [omitted for brevity] ... */
        };

        // Function to handle editable range values
        function makeRangeEditable() {
            const editableSpans = document.querySelectorAll('.editable-value');
    
            editableSpans.forEach(span => {
                span.style.cursor = 'pointer';
                span.addEventListener('click', () => {
                    const type = span.getAttribute('data-type');
                    let newMin = null;
                    let newMax = null;
            
                    if (type === 'year') {
                        newMin = prompt('Enter new minimum year:', document.getElementById('yearRangeMin').value);
                        newMax = prompt('Enter new maximum year:', document.getElementById('yearRangeMax').value);
                        if (newMin !== null && newMax !== null) {
                            newMin = parseInt(newMin);
                            newMax = parseInt(newMax);
                            if (!isNaN(newMin) && !isNaN(newMax) && newMin <= newMax) {
                                document.getElementById('yearRangeMin').value = newMin;
                                document.getElementById('yearRangeMax').value = newMax;
                                // applyFilters(); // Removed real-time update
                                updateSlidersDisplay();
                            } else {
                                alert('Invalid input. Please enter valid numbers where min ≤ max.');
                            }
                        }
                    } else if (type === 'mass') {
                        newMin = prompt('Enter new minimum mass (g):', document.getElementById('massRangeMin').value);
                        newMax = prompt('Enter new maximum mass (g):', document.getElementById('massRangeMax').value);
                        if (newMin !== null && newMax !== null) {
                            newMin = parseInt(newMin);
                            newMax = parseInt(newMax);
                            if (!isNaN(newMin) && !isNaN(newMax) && newMin <= newMax) {
                                document.getElementById('massRangeMin').value = newMin;
                                document.getElementById('massRangeMax').value = newMax;
                                // applyFilters(); // Removed real-time update
                                updateSlidersDisplay();
                            } else {
                                alert('Invalid input. Please enter valid numbers where min ≤ max.');
                            }
                        }
                    } else if (type === 'diameter') {
                        newMin = prompt('Enter new minimum diameter (km):', document.getElementById('diameterRangeMin').value);
                        newMax = prompt('Enter new maximum diameter (km):', document.getElementById('diameterRangeMax').value);
                        if (newMin !== null && newMax !== null) {
                            newMin = parseFloat(newMin);
                            newMax = parseFloat(newMax);
                            if (!isNaN(newMin) && !isNaN(newMax) && newMin <= newMax) {
                                document.getElementById('diameterRangeMin').value = newMin;
                                document.getElementById('diameterRangeMax').value = newMax;
                                // applyFilters(); // Removed real-time update
                                updateCraterSlidersDisplay();
                            } else {
                                alert('Invalid input. Please enter valid numbers where min ≤ max.');
                            }
                        }
                    } else if (type === 'age') {
                        newMin = prompt('Enter new minimum age (Myr):', document.getElementById('ageRangeMin').value);
                        newMax = prompt('Enter new maximum age (Myr):', document.getElementById('ageRangeMax').value);
                        if (newMin !== null && newMax !== null) {
                            newMin = parseFloat(newMin);
                            newMax = parseFloat(newMax);
                            if (!isNaN(newMin) && !isNaN(newMax) && newMin <= newMax) {
                                document.getElementById('ageRangeMin').value = newMin;
                                document.getElementById('ageRangeMax').value = newMax;
                                // applyFilters(); // Removed real-time update
                                updateCraterSlidersDisplay();
                            } else {
                                alert('Invalid input. Please enter valid numbers where min ≤ max.');
                            }
                        }
                    }
                });
            });
        }

        // Call the function after the DOM has loaded
        document.addEventListener('DOMContentLoaded', makeRangeEditable);

        function populateColorSchemeSelectors() {
            const meteoriteSelect = document.getElementById('meteoriteColorScheme');
            const craterSelect = document.getElementById('craterColorScheme');
            for (let scheme in colorSchemes) {
                const meteoriteOption = document.createElement('option');
                meteoriteOption.value = scheme;
                meteoriteOption.textContent = scheme;
                meteoriteSelect.appendChild(meteoriteOption);

                const craterOption = document.createElement('option');
                craterOption.value = scheme;
                craterOption.textContent = scheme;
                craterSelect.appendChild(craterOption);
            }
            meteoriteSelect.value = 'Default';
            craterSelect.value = 'Blue Scale';
        }

        function getMeteoriteColor(mass) {
            const selectedScheme = document.getElementById('meteoriteColorScheme').value;
            const scheme = colorSchemes[selectedScheme].colors;
            for (let i = 0; i < scheme.length; i++) {
                if (mass >= scheme[i].threshold) {
                    return scheme[i].color;
                }
            }
            return Cesium.Color.GRAY.withAlpha(0.6);
        }

        function getCraterColor(diameter) {
            const selectedScheme = document.getElementById('craterColorScheme').value;
            const scheme = colorSchemes[selectedScheme].craterColors;
            for (let i = 0; i < scheme.length; i++) {
                if (diameter >= scheme[i].threshold) {
                    return scheme[i].color;
                }
            }
            return Cesium.Color.GRAY.withAlpha(0.8);
        }

        function fetchAllMeteorites() {
            const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=50000';
            showLoadingIndicator(true); // Show loading
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    allMeteorites = data;
                    populateMeteoriteClassOptions();
                    initializeMeteoriteSliders();
                    initializeMeteoriteFilters();
                    populateTargetRockOptions();
                    populateCraterTypeOptions();
                    applyFilters();
                })
                .catch(error => {
                    console.error('Error fetching meteorite data:', error);
                })
                .finally(() => {
                    showLoadingIndicator(false); // Hide loading
                });
        }

        function applyFilters() {
            showLoadingIndicator(true); // Show loading
            let yearMin = parseInt(document.getElementById('yearRangeMin').value);
            let yearMax = parseInt(document.getElementById('yearRangeMax').value);
            let massMin = parseInt(document.getElementById('massRangeMin').value);
            let massMax = parseInt(document.getElementById('massRangeMax').value);

            let diameterMin = parseFloat(document.getElementById('diameterRangeMin').value);
            let diameterMax = parseFloat(document.getElementById('diameterRangeMax').value);
            let ageMin = parseFloat(document.getElementById('ageRangeMin').value);
            let ageMax = parseFloat(document.getElementById('ageRangeMax').value);
            const selectedRocks = Array.from(document.getElementById('targetRockSelect').selectedOptions).map(option => option.value);
            const selectedClasses = Array.from(document.getElementById('meteoriteClassSelect').selectedOptions).map(option => option.value);
            const selectedCraterTypes = Array.from(document.getElementById('craterTypeSelect').selectedOptions).map(option => option.value);

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
                const recclass = m.recclass || 'Unknown';

                const yearMatch = year ? (year >= yearMin && year <= yearMax) : true;
                const massMatch = mass ? (mass >= massMin && mass <= massMax) : true;
                const classMatch = selectedClasses.length ? selectedClasses.includes(recclass) : true;

                return yearMatch && massMatch && classMatch;
            });

            plottedMeteorites = filteredMeteorites.filter(m => {
                let lat, lon;

                if (m.geolocation) {
                    if (
                        m.geolocation.latitude !== undefined && 
                        m.geolocation.longitude !== undefined
                    ) {
                        lat = parseFloat(m.geolocation.latitude);
                        lon = parseFloat(m.geolocation.longitude);
                    } else if (
                        m.geolocation.coordinates && 
                        m.geolocation.coordinates.length === 2
                    ) {
                        lon = parseFloat(m.geolocation.coordinates[0]);
                        lat = parseFloat(m.geolocation.coordinates[1]);
                    }
                } else if (m.reclat && m.reclong) {
                    lat = parseFloat(m.reclat);
                    lon = parseFloat(m.reclong);
                }

                // Ensure lat and lon are valid numbers
                return !isNaN(lat) && !isNaN(lon);
            });

            filteredCraters = allCraters.filter(feature => {
                const properties = feature.properties;
                let diameter = parseFloat(properties['Crater diamter [km]']) || 0;
                let age_min = properties.age_min !== null ? parseFloat(properties.age_min) : minCraterAge;
                let age_max = properties.age_max !== null ? parseFloat(properties.age_max) : maxCraterAge;
                const targetRock = properties.Target || 'Unknown';
                const craterType = properties['Crater type'] || 'Unknown';

                const diameterMatch = diameter >= diameterMin && diameter <= diameterMax;
                const ageMatch = (age_max >= ageMin && age_min <= ageMax);
                const rockMatch = selectedRocks.length ? selectedRocks.includes(targetRock) : true;
                const typeMatch = selectedCraterTypes.length ? selectedCraterTypes.includes(craterType) : true;

                return diameterMatch && ageMatch && rockMatch && typeMatch;
            });

            updateMeteoriteData();
            updateCraterData();
            updateTopMeteorites();
            updateTopCraters();
            updateTotalCounts();
            updateModalTable();
            updateCraterModalTable();
            showLoadingIndicator(false); // Hide loading
        }

        function parse_age_values(age_str) {
            if (!age_str) return [null, null];
            age_str = age_str.trim();
            const match = age_str.match(/([><~]?)([\d\.]+)/);
            if (match) {
                const operator = match[1];
                const value = parseFloat(match[2]);
                if (operator === '>') return [value, 2500];
                if (operator === '<') return [0, value];
                return [value, value];
            }
            return [null, null];
        }

        function updateTotalCounts() {
            document.getElementById('totalMeteorites').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
            document.getElementById('totalCraters').innerText = `Total Impact Craters: ${filteredCraters.length}`;
        }

        function updateMeteoriteData() {
            meteoriteDataSource.entities.removeAll();
            meteoriteEntities = [];

            plottedMeteorites.forEach((meteorite, index) => {
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
                    const pointSize = mass !== 'Unknown' ? Math.min(Math.max(mass / 10000, 5), 20) : 5;
                    const entity = meteoriteDataSource.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: pointSize,
                            color: mass !== 'Unknown' ? getMeteoriteColor(mass) : Cesium.Color.GRAY.withAlpha(0.6)
                        },
                        properties: {
                            isMeteorite: true,
                            meteoriteIndex: filteredMeteorites.indexOf(meteorite)
                        }
                    });
                    meteoriteEntities.push(entity);
                }
            });

            meteoriteDataSource.clustering.enabled = document.getElementById('clusterMeteorites').checked;
            meteoriteDataSource.clustering.pixelRange = 45;
            meteoriteDataSource.clustering.minimumClusterSize = 10;
            meteoriteDataSource.clustering.clusterBillboards = true;
            meteoriteDataSource.clustering.clusterLabels = false;
            meteoriteDataSource.clustering.clusterPoints = true;

            meteoriteDataSource.clustering.eventHandler = createClusterEventHandler(meteoriteDataSource.clustering);
        }

        function createClusterEventHandler(clustering) {
            clustering.clusterEvent.addEventListener(function(clusteredEntities, cluster) {
                cluster.label.show = false;
                cluster.billboard.show = true;
                cluster.billboard.id = cluster;

                const clusterSize = clusteredEntities.length;
                cluster.billboard.image = createClusterIcon(clusterSize);
            });
        }

        function createClusterIcon(clusterSize) {
            const digits = clusterSize.toString().length;
            const size = 20 + (digits * 5);
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = size;
            const context = canvas.getContext('2d');

            context.fillStyle = 'rgba(255, 165, 0, 0.7)';
            context.beginPath();
            context.arc(size/2, size/2, size/2, 0, 2 * Math.PI);
            context.fill();

            context.fillStyle = 'black';
            context.font = `bold ${10 + (digits * 2)}px sans-serif`;
            context.textAlign = 'center';
            context.textBaseline = 'middle';
            context.fillText(clusterSize, size/2, size/2);

            return canvas.toDataURL();
        }

        function updateClusteringOnZoom() {
            const altitude = viewer.camera.positionCartographic.height;
            if (altitude < 500000) {
                meteoriteDataSource.clustering.enabled = false;
            } else {
                meteoriteDataSource.clustering.enabled = document.getElementById('clusterMeteorites').checked;
            }
        }

        viewer.camera.changed.addEventListener(updateClusteringOnZoom);

        function updateCraterData() {
            craterEntities.entities.removeAll();
            craterEntitiesList = [];

            filteredCraters.forEach((feature, index) => {
                const properties = feature.properties;
                const geometry = feature.geometry;

                let lon, lat;

                if (geometry && geometry.type === "Point") {
                    [lon, lat] = geometry.coordinates;
                } else if (properties.Longitude && properties.Latitude) {
                    lon = parseFloat(properties.Longitude);
                    lat = parseFloat(properties.Latitude);
                } else {
                    console.warn(`Crater ${properties.Name} has no valid geometry.`);
                    return;
                }

                if (isNaN(lat) || isNaN(lon)) {
                    console.warn(`Invalid coordinates for crater ${properties.Name}.`);
                    return;
                }

                let diameter = parseFloat(properties['Crater diamter [km]']) || 1;

                const entity = craterEntities.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(lon, lat),
                    point: {
                        pixelSize: getCraterSize(diameter),
                        color: getCraterColor(diameter),
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 1
                    },
                    description: getCraterDescription(properties),
                    properties: {
                        isImpactCrater: true,
                        craterIndex: index
                    }
                });
                craterEntitiesList.push(entity);
            });
        }
        
        function getCraterDescription(properties) {
            const name = properties.Name || 'Unknown';
            const age = properties['Age [Myr]'] || 'Unknown';
            const diameter = properties['Crater diamter [km]'] || 'Unknown';
            const country = properties.Country || 'Unknown';
            const target = properties.Target || 'Unknown';
            const type = properties['Crater type'] || 'Unknown';

            return `
                <b>Name:</b> ${name}<br>
                <b>Age:</b> ${age} Myr<br>
                <b>Diameter:</b> ${diameter} km<br>
                <b>Country:</b> ${country}<br>
                <b>Target:</b> ${target}<br>
                <b>Type:</b> ${type}<br>
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
            if (diameter >= 200) return 30;
            if (diameter >= 150) return 25;
            if (diameter >= 100) return 20;
            if (diameter >= 50) return 15;
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
            const sortedCraters = filteredCraters.filter(c => c.properties['Crater diamter [km]']).sort((a, b) => parseFloat(b.properties['Crater diamter [km]']) - parseFloat(a.properties['Crater diamter [km]']));
            const top10Craters = sortedCraters.slice(0, 10);
            const craterBar = document.getElementById('craterBar');
            craterBar.innerHTML = '<div class="bar-item"><strong>Top Impact Craters:</strong></div>';

            const viewAllCraters = document.createElement('div');
            viewAllCraters.className = 'bar-item';
            viewAllCraters.innerHTML = `<strong>View All</strong>`;
            viewAllCraters.onclick = () => openCraterModal();
            craterBar.appendChild(viewAllCraters);

            top10Craters.forEach((crater, index) => {
                const name = crater.properties.Name || 'Unknown';
                const diameter = parseFloat(crater.properties['Crater diamter [km]']) || 0;
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
                    orientation: { heading: Cesium.Math.toRadians(0), pitch: Cesium.Math.toRadians(-90) }
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
                orientation: { heading: Cesium.Math.toRadians(0), pitch: Cesium.Math.toRadians(-90) }
            });
        }

        function openModal() {
            updateModalTable();
            document.getElementById('modal').style.display = 'block';
            // Clear existing highlights
            const rows = document.querySelectorAll('#fullMeteoriteTable tbody tr');
            rows.forEach(row => row.style.backgroundColor = '');
        }
    
        function openCraterModal() {
            updateCraterModalTable();
            document.getElementById('craterModal').style.display = 'block';
            // Clear existing highlights
            const rows = document.querySelectorAll('#fullCraterTable tbody tr');
            rows.forEach(row => row.style.backgroundColor = '');
        }

        const tooltip = document.getElementById('tooltip');
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

        handler.setInputAction(movement => {
            const pickedObject = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(pickedObject)) {
                let id = pickedObject.id;
                if (id && (id.properties && (id.properties.isMeteorite || id.properties.isImpactCrater))) {
                    tooltip.style.display = 'block';
                    if (id.properties.isImpactCrater) {
                        tooltip.innerHTML = id.description.getValue();
                    } else if (id.properties.isMeteorite) {
                        const index = id.properties.meteoriteIndex;
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

        // Double-click event handler
        handler.setInputAction((movement) => {
            const pickedObject = viewer.scene.pick(movement.position);
            if (Cesium.defined(pickedObject)) {
                const id = pickedObject.id;
                if (Cesium.defined(id) && Cesium.defined(id.properties)) {
                    if (id.properties.isMeteorite) {
                        const index = id.properties.meteoriteIndex;
                        openModal(); // Open meteorite modal
                        setTimeout(() => {
                            const table = document.getElementById('fullMeteoriteTable');
                            const row = table.querySelector(`tr[data-index='${index}']`);
                            if (row) {
                                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                row.classList.add('highlighted-row'); // Add highlight class
                                setTimeout(() => { row.classList.remove('highlighted-row'); }, 2000); // Remove after 2 seconds
                            }
                        }, 300); // Slight delay to ensure modal is open
                    } else if (id.properties.isImpactCrater) {
                        const index = id.properties.craterIndex;
                        openCraterModal(); // Open crater modal
                        setTimeout(() => {
                            const table = document.getElementById('fullCraterTable');
                            const row = table.querySelector(`tr[data-index='${index}']`);
                            if (row) {
                                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                row.classList.add('highlighted-row'); // Add highlight class
                                setTimeout(() => { row.classList.remove('highlighted-row'); }, 2000); // Remove after 2 seconds
                            }
                        }, 300); // Slight delay to ensure modal is open
                    }
                }
            }
        }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);

        window.flyToMeteorite = flyToMeteorite;
        window.flyToCrater = flyToCrater;

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
        document.getElementById('closeModal').onclick = () => modal.style.display = 'none';
        document.getElementById('closeCraterModal').onclick = () => craterModal.style.display = 'none';
        window.onclick = event => {
            if (event.target == modal) modal.style.display = 'none';
            if (event.target == craterModal) craterModal.style.display = 'none';
            if (event.target == infoModal) infoModal.style.display = 'none';
        };

        function updateModalTable() {
                const tbody = document.querySelector('#fullMeteoriteTable tbody');
                if (!filteredMeteorites.length) {
                    tbody.innerHTML = '<tr><td colspan="6">No meteorite data available.</td></tr>';
                    return;
                }
                const searchQuery = document.getElementById('meteoriteSearchInput').value.toLowerCase();
                tbody.innerHTML = '';
    
                filteredMeteorites.forEach((meteorite, index) => {
                    const name = meteorite.name || 'Unknown';
                    if (name.toLowerCase().includes(searchQuery)) {
                        const id = meteorite.id || 'Unknown';
                        const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                        const massDisplay = formatMass(mass);
                        const recclass = meteorite.recclass || 'Unknown';
                        const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                        const fall = meteorite.fall || 'Unknown';
                        const metBullLink = id !== 'Unknown' ? `<a href="https://www.lpi.usra.edu/meteor/metbull.php?code=${id}" target="_blank">View</a>` : 'N/A';
    
                        const tr = document.createElement('tr');
                        tr.style.cursor = 'pointer';
                        tr.setAttribute('data-index', index); // Add data-index attribute
                        tr.onclick = () => {
                            flyToMeteorite(index);
                            document.getElementById('modal').style.display = 'none'; // Close modal
                        };
                        tr.innerHTML = `
                            <td>${name}</td>
                            <td>${massDisplay}</td>
                            <td>${recclass}</td>
                            <td>${year}</td>
                            <td>${fall}</td>
                            <td>${metBullLink}</td>
                        `;
                        tbody.appendChild(tr);
                    }
                });
            }

        function updateCraterModalTable() {
                const tbody = document.querySelector('#fullCraterTable tbody');
                const thead = document.querySelector('#fullCraterTable thead');
                const headerRow = document.getElementById('craterTableHeaders');
                if (!filteredCraters.length) {
                    tbody.innerHTML = '<tr><td colspan="5">No crater data available.</td></tr>';
                    return;
                }
                const searchQuery = document.getElementById('craterSearchInput').value.toLowerCase();
                tbody.innerHTML = '';
                headerRow.innerHTML = '';
    
                // Populate table headers
                const filteredPropertyNames = craterPropertyNames.filter(propName => propName !== 'age_max' && propName !== 'age_min');
                filteredPropertyNames.forEach((propName, index) => {
                    const th = document.createElement('th');
                    th.innerHTML = `${propName} &#x25B2;&#x25BC;`;
                    th.onclick = () => sortCraterTable(index);
                    headerRow.appendChild(th);
                });
    
                filteredCraters.forEach((crater, index) => {
                    const properties = crater.properties;
                    const name = properties.Name || 'Unknown';
                    if (name.toLowerCase().includes(searchQuery)) {
                        const tr = document.createElement('tr');
                        tr.style.cursor = 'pointer';
                        tr.setAttribute('data-index', index); // Add data-index attribute
                        tr.onclick = () => {
                            flyToCrater(index);
                            document.getElementById('craterModal').style.display = 'none'; // Close crater modal
                         };
                        filteredPropertyNames.forEach(propName => {
                            const td = document.createElement('td');
                            const value = properties[propName] !== undefined ? properties[propName] : 'Unknown';
                            if (propName === 'Name') {
                                const id = properties.No || '';
                                td.innerHTML = `<a href="https://impact-craters.com/craters_id${id}" target="_blank">${value}</a>`;
                            } else {
                                td.innerText = value;
                            }
                            tr.appendChild(td);
                        });
                        tbody.appendChild(tr);
                    }
                });
            }

        function sortTable(tableId, colIndex) {
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.rows);
            let dir = table.getAttribute('data-sort-dir') === 'asc' ? 'desc' : 'asc';
            table.setAttribute('data-sort-dir', dir);

            rows.sort((a, b) => {
                let x = a.cells[colIndex].innerText || a.cells[colIndex].textContent;
                let y = b.cells[colIndex].innerText || b.cells[colIndex].textContent;
       
                if (colIndex === 5) {
                    return 0;
                }
                const xNum = parseFloat(x.replace(/[^\d.-]/g, ''));
                const yNum = parseFloat(y.replace(/[^\d.-]/g, ''));

                if (!isNaN(xNum) && !isNaN(yNum)) {
                    return dir === 'asc' ? xNum - yNum : yNum - xNum;
                } else {
                    x = x.toLowerCase();
                    y = y.toLowerCase();
                    if (x < y) return dir === 'asc' ? -1 : 1;
                    if (x > y) return dir === 'asc' ? 1 : -1;
                    return 0;
                }
            });

            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        }

        function sortCraterTable(colIndex) {
            const table = document.getElementById('fullCraterTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.rows);
            let dir = table.getAttribute('data-sort-dir') === 'asc' ? 'desc' : 'asc';
            table.setAttribute('data-sort-dir', dir);

            rows.sort((a, b) => {
                let x = a.cells[colIndex].innerText || a.cells[colIndex].textContent;
                let y = b.cells[colIndex].innerText || b.cells[colIndex].textContent;

                const xNum = parseFloat(x.replace(/[^\d.-]/g, ''));
                const yNum = parseFloat(y.replace(/[^\d.-]/g, ''));

                if (!isNaN(xNum) && !isNaN(yNum)) {
                    return dir === 'asc' ? xNum - yNum : yNum - xNum;
                } else {
                    x = x.toLowerCase();
                    y = y.toLowerCase();
                    if (x < y) return dir === 'asc' ? -1 : 1;
                    if (x > y) return dir === 'asc' ? 1 : -1;
                    return 0;
                }
            });

            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        }

        document.getElementById('meteoriteSearchInput').addEventListener('input', updateModalTable);
        document.getElementById('craterSearchInput').addEventListener('input', updateCraterModalTable);

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
                            orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(-90) }
                        });
                    } else {
                        alert('Location not found.');
                    }
                })
                .catch(error => {
                    console.error('Error searching location:', error);
                });
        }

        function initializeSliders() {
            initializeMeteoriteSliders();
            initializeCraterSliders();
        }

        function initializeMeteoriteSliders() {
            const years = allMeteorites.map(m => m.year ? new Date(m.year).getFullYear() : null).filter(y => y !== null);
            const masses = allMeteorites.map(m => m.mass ? parseFloat(m.mass) : null).filter(m => m !== null);

            const minYear = Math.min(...years);
            const maxYear = Math.max(...years);
            const minMass = Math.min(...masses);
            const maxMass = Math.max(...masses);

            document.getElementById('yearRangeMin').min = minYear;
            document.getElementById('yearRangeMin').max = maxYear;
            document.getElementById('yearRangeMax').min = minYear;
            document.getElementById('yearRangeMax').max = maxYear;
            document.getElementById('yearRangeMin').value = minYear;
            document.getElementById('yearRangeMax').value = maxYear;

            document.getElementById('massRangeMin').min = minMass;
            document.getElementById('massRangeMin').max = maxMass;
            document.getElementById('massRangeMax').min = minMass;
            document.getElementById('massRangeMax').max = maxMass;
            document.getElementById('massRangeMin').value = minMass;
            document.getElementById('massRangeMax').value = maxMass;

            updateSlidersDisplay();
        }

        function initializeCraterSliders() {
            const diameters = allCraters
                .map(c => c.properties['Crater diamter [km]'] ? parseFloat(c.properties['Crater diamter [km]']) : null)
                .filter(d => d !== null && !isNaN(d));
            const ages = allCraters
                .map(c => c.properties.age_min !== null ? parseFloat(c.properties.age_min) : null)
                .filter(a => a !== null && !isNaN(a));

            if (diameters.length === 0) {
                console.warn('No crater diameters found.');
                return;
            }

            const minDiameter = Math.min(...diameters);
            const sliderMaxDiameter = 280; // Manually set the upper diameter limit to 280 km
            const minAge = Math.min(...ages);
            const maxAge = Math.max(...ages);

            const diameterRangeMin = document.getElementById('diameterRangeMin');
            const diameterRangeMax = document.getElementById('diameterRangeMax');
            const ageRangeMin = document.getElementById('ageRangeMin');
            const ageRangeMax = document.getElementById('ageRangeMax');

            // Set diameter sliders with manual upper limit
            diameterRangeMin.min = minDiameter;
            diameterRangeMin.max = sliderMaxDiameter;
            diameterRangeMin.value = minDiameter;

            diameterRangeMax.min = minDiameter;
            diameterRangeMax.max = sliderMaxDiameter;
            diameterRangeMax.value = sliderMaxDiameter;

            // Set age sliders
            ageRangeMin.min = minAge;
            ageRangeMin.max = maxAge;
            ageRangeMin.value = minAge;

            ageRangeMax.min = minAge;
            ageRangeMax.max = maxAge;
            ageRangeMax.value = maxAge;

            updateCraterSlidersDisplay();
        }

        document.getElementById('yearRangeMin').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateSlidersDisplay();
        });
        document.getElementById('yearRangeMax').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateSlidersDisplay();
        });
        document.getElementById('massRangeMin').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateSlidersDisplay();
        });
        document.getElementById('massRangeMax').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateSlidersDisplay();
        });

        document.getElementById('diameterRangeMin').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateCraterSlidersDisplay();
        });
        document.getElementById('diameterRangeMax').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateCraterSlidersDisplay();
        });
        document.getElementById('ageRangeMin').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateCraterSlidersDisplay();
        });
        document.getElementById('ageRangeMax').addEventListener('input', () => {
            // applyFilters(); // Removed real-time update
            updateCraterSlidersDisplay();
        });
        document.getElementById('targetRockSelect').addEventListener('change', () => {
            // applyFilters(); // Removed real-time update
        });
        document.getElementById('meteoriteClassSelect').addEventListener('change', () => {
            // applyFilters(); // Removed real-time update
        });

        document.getElementById('toggleMeteorites').addEventListener('change', function() {
            meteoriteDataSource.show = this.checked;
        });

        document.getElementById('clusterMeteorites').addEventListener('change', function() {
            meteoriteDataSource.clustering.enabled = this.checked;
        });

        document.getElementById('toggleCraters').addEventListener('change', function() {
            craterEntities.show = this.checked;
        });

        document.getElementById('refreshButton').onclick = resetFilters;

        function resetFilters() {
            initializeSliders();

            const targetRockSelect = document.getElementById('targetRockSelect');
            for (let i = 0; i < targetRockSelect.options.length; i++) {
                targetRockSelect.options[i].selected = false;
            }

            const craterTypeSelect = document.getElementById('craterTypeSelect');
            for (let i = 0; i < craterTypeSelect.options.length; i++) {
                craterTypeSelect.options[i].selected = false;
            }

            const meteoriteClassSelect = document.getElementById('meteoriteClassSelect');
            for (let i = 0; i < meteoriteClassSelect.options.length; i++) {
                meteoriteClassSelect.options[i].selected = false;
            }

            applyFilters();
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
            const diameterMin = parseFloat(document.getElementById('diameterRangeMin').value);
            const diameterMax = parseFloat(document.getElementById('diameterRangeMax').value);
            document.getElementById('diameterRangeValue').innerText = `${diameterMin.toFixed(2)} - ${diameterMax.toFixed(2)} km`;

            const ageMin = parseFloat(document.getElementById('ageRangeMin').value);
            const ageMax = parseFloat(document.getElementById('ageRangeMax').value);
            document.getElementById('ageRangeValue').innerText = `${ageMin.toFixed(0)} - ${ageMax.toFixed(0)} Myr`;
        }

        function populateTargetRockOptions() {
            const targetRockSet = new Set();
            allCraters.forEach(crater => {
                const targetRock = crater.properties.Target || 'Unknown';
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

        function populateMeteoriteClassOptions() {
            const classSet = new Set();
            allMeteorites.forEach(meteorite => {
                const recclass = meteorite.recclass || 'Unknown';
                classSet.add(recclass);
            });
            const meteoriteClassSelect = document.getElementById('meteoriteClassSelect');
            classSet.forEach(cls => {
                const option = document.createElement('option');
                option.value = cls;
                option.text = cls;
                meteoriteClassSelect.add(option);
            });
        }

        // Add function to populate crater type options
        function populateCraterTypeOptions() {
            const craterTypeSet = new Set();
            allCraters.forEach(crater => {
                const craterType = crater.properties['Crater type'] || 'Unknown';
                craterTypeSet.add(craterType);
            });
            const craterTypeSelect = document.getElementById('craterTypeSelect');
            craterTypeSet.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.text = type;
                craterTypeSelect.add(option);
            });
        }

        function initializeCraterFilters() {
            populateTargetRockOptions();
            populateCraterTypeOptions();
            initializeCraterSliders();
        }

        // Add event listener for crater type select
        document.getElementById('craterTypeSelect').addEventListener('change', () => {
            // applyFilters(); // Removed real-time update
        });

        // In resetFilters function, reset crater type select
        function resetFilters() {
            initializeSliders();

            const targetRockSelect = document.getElementById('targetRockSelect');
            for (let i = 0; i < targetRockSelect.options.length; i++) {
                targetRockSelect.options[i].selected = false;
            }

            const craterTypeSelect = document.getElementById('craterTypeSelect');
            for (let i = 0; i < craterTypeSelect.options.length; i++) {
                craterTypeSelect.options[i].selected = false;
            }

            const meteoriteClassSelect = document.getElementById('meteoriteClassSelect');
            for (let i = 0; i < meteoriteClassSelect.options.length; i++) {
                meteoriteClassSelect.options[i].selected = false;
            }

            applyFilters();
        }

        // Adjust getCraterSize function to use dynamic thresholds based on data
        function getCraterSize(diameter) {
            if (diameter >= 200) return 30;
            if (diameter >= 150) return 25;
            if (diameter >= 100) return 20;
            if (diameter >= 50) return 15;
            return 10;
        }

        function initializeMeteoriteFilters() {
            populateMeteoriteClassOptions();
            initializeMeteoriteSliders();
        }

        initializeSliders();
        initializeCraterFilters();
        populateColorSchemeSelectors();

        fetchAllMeteorites();

        const infoModal = document.getElementById('infoModal');
        const infoButton = document.getElementById('infoButton');
        const closeInfoModal = document.getElementById('closeInfoModal');

        infoButton.onclick = () => {
            closeOtherMenus('info');
            infoModal.style.display = 'block';
        };

        closeInfoModal.onclick = () => {
            infoModal.style.display = 'none';
        };

        const optionsButton = document.getElementById('optionsButton');
        const controls = document.getElementById('controls');
        const closeOptions = document.getElementById('closeOptions');
        const applyFiltersButton = document.getElementById('applyFiltersButton'); // Apply Button

        optionsButton.onclick = () => {
            if (controls.style.display === 'none' || controls.style.display === '') {
                closeOtherMenus('options');
                controls.style.display = 'block';
                applyFiltersButton.style.display = 'inline-block'; // Show Apply button
            } else {
                controls.style.display = 'none';
                applyFilters();
                applyFiltersButton.style.display = 'none'; // Hide Apply button
            }
        };

        closeOptions.onclick = () => {
            controls.style.display = 'none';
            applyFilters();
            applyFiltersButton.style.display = 'none'; // Hide Apply button
        };

        const keyButton = document.getElementById('keyButton');
        const keyMenu = document.getElementById('keyMenu');
        const closeKeyMenu = document.getElementById('closeKeyMenu');

        keyButton.onclick = () => {
            if (keyMenu.style.display === 'none' || keyMenu.style.display === '') {
                closeOtherMenus('key');
                keyMenu.style.display = 'block';
                updateMeteoriteLegend();
                updateCraterLegend();
            } else {
                keyMenu.style.display = 'none';
            }
        };

        closeKeyMenu.onclick = () => {
            keyMenu.style.display = 'none';
        };

        function closeOtherMenus(openedMenu) {
            if (openedMenu !== 'options') controls.style.display = 'none';
            if (openedMenu !== 'key') keyMenu.style.display = 'none';
            if (openedMenu !== 'info') infoModal.style.display = 'none';
        }

        document.getElementById('meteoriteColorScheme').onchange = function() {
            applyFilters();
            updateMeteoriteLegend();
        };

        document.getElementById('craterColorScheme').onchange = function() {
            applyFilters();
            updateCraterLegend();
        };

        document.getElementById('resetColorSchemes').onclick = function() {
            document.getElementById('meteoriteColorScheme').value = 'Default';
            document.getElementById('craterColorScheme').value = 'Blue Scale';
            applyFilters();
            updateMeteoriteLegend();
            updateCraterLegend();
        };

        function updateCraterLegend() {
            const legendContainer = document.getElementById('craterLegend');
            legendContainer.innerHTML = '<h3>💥 Impact Craters</h3><ul class="legend-list"></ul>';
            const list = legendContainer.querySelector('.legend-list');
            const selectedScheme = document.getElementById('craterColorScheme').value;
            const scheme = colorSchemes[selectedScheme].craterColors;

            // Sort the scheme by threshold ascending
            const sortedScheme = scheme.slice().sort((a, b) => a.threshold - b.threshold);

            sortedScheme.forEach((item, index) => {
                const li = document.createElement('li');
                li.innerHTML = `<span class="legend-icon" style="background-color: ${item.color.toCssColorString()};"></span>`;
                let label = '';

                if (index === 0) {
                    label = `Diameter < ${sortedScheme[1].threshold} km`;
                } else {
                    label = `Diameter ≥ ${item.threshold} km`;
                }

                li.innerHTML += label;
                list.appendChild(li);
            });
        }
        
        // Function to close other menus when one is opened
        function closeOtherMenus(openedMenu) {
            if (openedMenu !== 'options') controls.style.display = 'none';
            if (openedMenu !== 'key') keyMenu.style.display = 'none';
            if (openedMenu !== 'info') infoModal.style.display = 'none';
        }
    
        // Get the wrapper element
        const wrapper = document.getElementById('wrapper');
        const fullscreenButton = document.getElementById('fullscreenButton');

        fullscreenButton.onclick = () => {
            if (!document.fullscreenElement) {
                wrapper.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        };

        document.addEventListener('fullscreenchange', () => {
             if (document.fullscreenElement) {
                fullscreenButton.textContent = '🡼 Exit Fullscreen';
            } else {
                fullscreenButton.textContent = '⛶ Fullscreen';
            }
        });

        function updateMeteoriteLegend() {
            const legendContainer = document.getElementById('meteoriteLegend');
            legendContainer.innerHTML = '<h3>🌠 Meteorites</h3><ul class="legend-list"></ul>';
            const list = legendContainer.querySelector('.legend-list');
            const selectedScheme = document.getElementById('meteoriteColorScheme').value;
            const scheme = colorSchemes[selectedScheme].colors;

            // Sort the scheme by threshold ascending
            const sortedScheme = scheme.slice().sort((a, b) => a.threshold - b.threshold);

            sortedScheme.forEach((item, index) => {
                const li = document.createElement('li');
                li.innerHTML = `<span class="legend-icon" style="background-color: ${item.color.toCssColorString()};"></span>`;
                let label = '';

                if (index === 0) {
                    label = `Mass < ${(sortedScheme[1].threshold / 1000).toLocaleString()} kg`;
                } else {
                    label = `Mass ≥ ${(item.threshold / 1000).toLocaleString()} kg`;
                }

                li.innerHTML += label;
                list.appendChild(li);
            });
        }

        // Loading Indicator Functions
        function showLoadingIndicator(show) {
            const indicator = document.getElementById('loadingIndicator');
            indicator.style.display = show ? 'block' : 'none';
        }

        // Apply Filters Button Event
        applyFiltersButton.onclick = () => {
            applyFilters();
            controls.style.display = 'none';
            applyFiltersButton.style.display = 'none';
        };

        function updateCraterLegend() {
            const legendContainer = document.getElementById('craterLegend');
            legendContainer.innerHTML = '<h3>💥 Impact Craters</h3><ul class="legend-list"></ul>';
            const list = legendContainer.querySelector('.legend-list');
            const selectedScheme = document.getElementById('craterColorScheme').value;
            const scheme = colorSchemes[selectedScheme].craterColors;

            // Sort the scheme by threshold ascending
            const sortedScheme = scheme.slice().sort((a, b) => a.threshold - b.threshold);

            sortedScheme.forEach((item, index) => {
                const li = document.createElement('li');
                li.innerHTML = `<span class="legend-icon" style="background-color: ${item.color.toCssColorString()};"></span>`;
                let label = '';

                if (index === 0) {
                    label = `Diameter < ${sortedScheme[1].threshold} km`;
                } else {
                    label = `Diameter ≥ ${item.threshold} km`;
                }

                li.innerHTML += label;
                list.appendChild(li);
            });
        }

        updateMeteoriteLegend();
        updateCraterLegend();
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
