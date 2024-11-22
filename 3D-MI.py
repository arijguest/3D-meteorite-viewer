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
                return float(groups['min']), 2500
            elif 'max' in groups and groups['max']:
                return 0, float(groups['max'])
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
        /* Remove display: block to align columns */
        /* #fullMeteoriteTable tbody, #fullCraterTable tbody {
            display: block;
            max-height: 60vh;
            overflow-y: auto;
        }
        #fullMeteoriteTable thead, #fullCraterTable thead {
            display: table;
            width: 100%;
            table-layout: auto;
        }
        #fullMeteoriteTable tbody tr, #fullCraterTable tbody tr {
            display: table;
            width: 100%;
            table-layout: auto;
        } */
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
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="header">
        <h1>🌠 Global Meteorite Specimens & Impact Craters 🌠</h1>
        <div>
            <button id="optionsButton">⚙️ Options</button>
            <button id="keyButton">🔑 Key</button>
            <button id="infoButton">ℹ️ Info</button>
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
            <label><strong>Year Range:</strong> <span id="yearRangeValue"></span></label>
            <input type="range" id="yearRangeMin" min="860" max="2023" value="860">
            <input type="range" id="yearRangeMax" min="860" max="2023" value="2023">
        </div>
        <div>
            <label><strong>Mass Range:</strong> <span id="massRangeValue"></span></label>
            <input type="range" id="massRangeMin" min="0" max="60000000" value="0">
            <input type="range" id="massRangeMax" min="0" max="60000000" value="60000000">
        </div>
        <div>
            <label><strong>Meteorite Class:</strong></label>
            <select id="meteoriteClassSelect" multiple size="5"></select>
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
            <label><strong>Diameter Range (km):</strong> <span id="diameterRangeValue"></span></label>
            <input type="range" id="diameterRangeMin" value="0">
            <input type="range" id="diameterRangeMax" value="300">
        </div>
        <div>
            <label><strong>Age Range:</strong> <span id="ageRangeValue"></span></label>
            <input type="range" id="ageRangeMin" value="0">
            <input type="range" id="ageRangeMax" value="2500">
        </div>
        <div>
            <label><strong>Target Rock:</strong></label>
            <select id="targetRockSelect" multiple size="5"></select>
        </div>
        <div>
            <label><strong>Crater Type:</strong></label>
            <select id="craterTypeSelect" multiple size="5"></select>
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
            <p>Data source: <a href="https://doi.org/10.1111/maps.13657" target="_blank">Kenkmann 2021 "The terrestrial impact crater record: A statistical analysis of morphologies, structures, ages, lithologies, and more"</a>. Website created by <a href="https://impact-craters.com/" target="_blank">Dr. Matthias Ebert</a>.</p>
        </div>
    </div>
    <div id="infoModal">
        <div id="infoModal-content">
            <span id="closeInfoModal">&times;</span>
            <h2>Information</h2>
            <p>Welcome to the Global Meteorite Specimens and Impact Craters Visualization. This interactive tool allows you to explore meteorite landings recorded by NASA and discover impact craters around the world.</p>
            <h3>Features:</h3>
            <ul>
                <li><strong>Navigation:</strong> Use mouse or touch controls to rotate, zoom, and pan around the globe.</li>
                <li><strong>Search:</strong> Fly to a specific location using the search bar in the Options menu.</li>
                <li><strong>Filters:</strong> Adjust filters like year, mass, diameter, age, class, and target rock type in the Options menu to refine the displayed data.</li>
                <li><strong>Show/Hide Data:</strong> Toggle meteorites and impact craters visibility using the checkboxes in the Options menu.</li>
                <li><strong>Color Schemes:</strong> Customize color schemes for meteorites and impact craters in the Key menu. Choose from various palettes, including colorblind-friendly options.</li>
                <li><strong>Legends:</strong> View legends for meteorite and crater color schemes in the Key menu to understand data representation.</li>
                <li><strong>Clustering:</strong> Enable or disable clustering of meteorite markers to manage display density at different zoom levels.</li>
                <li><strong>Top Lists:</strong> Explore top meteorites and impact craters in the bars at the bottom and top of the screen, respectively. Click to fly to their locations.</li>
                <li><strong>Details:</strong> Click on any meteorite or crater marker to view detailed information in a tooltip.</li>
                <li><strong>View All:</strong> Access full lists of meteorites and craters by clicking "View All" in the respective bars.</li>
                <li><strong>Reset Filters:</strong> Quickly reset all filters to default settings using the "Reset Filters" button.</li>
                <li><strong>Reset Color Schemes:</strong> Reset the color schemes for meteorites and impact craters to default settings using the "Reset Color Schemes" button in the Key menu.</li>
            </ul>
            <h3>Data Sources:</h3>
            <ul>
                <li><a href="https://data.nasa.gov/Space-Science/Meteorite-Landings/gh4g-9sfh" target="_blank">NASA Meteorite Landings Dataset</a></li>
                <li>Impact Crater data from <a href="https://doi.org/10.1111/maps.13657" target="_blank">Kenkmann 2021</a> and the website created by <a href="https://impact-craters.com/" target="_blank">Dr. Matthias Ebert</a></li>
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
                name: 'Default',
                description: 'Red to Yellow Scale',
                colors: [
                    { threshold: 500000, color: Cesium.Color.RED.withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.ORANGE.withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.YELLOW.withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.LIGHTYELLOW.withAlpha(0.6) },
                    { threshold: 0,      color: Cesium.Color.WHITE.withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 200, color: Cesium.Color.RED.withAlpha(0.8) },
                    { threshold: 100, color: Cesium.Color.ORANGE.withAlpha(0.8) },
                    { threshold: 50,  color: Cesium.Color.YELLOW.withAlpha(0.8) },
                    { threshold: 0,   color: Cesium.Color.LIGHTYELLOW.withAlpha(0.8) }
                ]
            },
            'Blue Scale': {
                name: 'Blue Scale',
                description: 'Dark Blue to Light Blue',
                colors: [
                    { threshold: 500000, color: Cesium.Color.DARKBLUE.withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.BLUE.withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.SKYBLUE.withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.CYAN.withAlpha(0.6) },
                    { threshold: 0,      color: Cesium.Color.LIGHTCYAN.withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 50, color: Cesium.Color.DARKBLUE.withAlpha(0.8) },
                    { threshold: 30, color: Cesium.Color.BLUE.withAlpha(0.8) },
                    { threshold: 10, color: Cesium.Color.SKYBLUE.withAlpha(0.8) },
                    { threshold: 0,  color: Cesium.Color.LIGHTBLUE.withAlpha(0.8) }
                ]
            },
            'Green Scale': {
                name: 'Green Scale',
                description: 'Dark Green to Light Green',
                colors: [
                    { threshold: 500000, color: Cesium.Color.DARKGREEN.withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.GREEN.withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.LIME.withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.LIGHTGREEN.withAlpha(0.6) },
                    { threshold: 0,      color: Cesium.Color.YELLOWGREEN.withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 50, color: Cesium.Color.DARKGREEN.withAlpha(0.8) },
                    { threshold: 30, color: Cesium.Color.GREEN.withAlpha(0.8) },
                    { threshold: 10, color: Cesium.Color.LIME.withAlpha(0.8) },
                    { threshold: 0,  color: Cesium.Color.LIGHTGREEN.withAlpha(0.8) }
                ]
            },
            'Purple Scale': {
                name: 'Purple Scale',
                description: 'Dark Purple to Light Purple',
                colors: [
                    { threshold: 500000, color: Cesium.Color.DARKVIOLET.withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.BLUEVIOLET.withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.VIOLET.withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.PLUM.withAlpha(0.6) },
                    { threshold: 0,      color: Cesium.Color.LAVENDER.withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 50, color: Cesium.Color.DARKVIOLET.withAlpha(0.8) },
                    { threshold: 30, color: Cesium.Color.BLUEVIOLET.withAlpha(0.8) },
                    { threshold: 10, color: Cesium.Color.VIOLET.withAlpha(0.8) },
                    { threshold: 0,  color: Cesium.Color.PLUM.withAlpha(0.8) }
                ]
            },
            'Brown Scale': {
                name: 'Brown Scale',
                description: 'Dark Brown to Light Brown',
                colors: [
                    { threshold: 500000, color: Cesium.Color.SIENNA.withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.SADDLEBROWN.withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.PERU.withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.BURLYWOOD.withAlpha(0.6) },
                    { threshold: 0,      color: Cesium.Color.WHEAT.withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 50, color: Cesium.Color.SIENNA.withAlpha(0.8) },
                    { threshold: 30, color: Cesium.Color.SADDLEBROWN.withAlpha(0.8) },
                    { threshold: 10, color: Cesium.Color.PERU.withAlpha(0.8) },
                    { threshold: 0,  color: Cesium.Color.BURLYWOOD.withAlpha(0.8) }
                ]
            },
            'Colorblind-Friendly (Deutan)': {
                name: 'Colorblind-Friendly (Deutan)',
                description: 'Accessible palette for deuteranomaly',
                colors: [
                    { threshold: 500000, color: Cesium.Color.fromCssColorString('#CC79A7').withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.fromCssColorString('#0072B2').withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.fromCssColorString('#009E73').withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.fromCssColorString('#D55E00').withAlpha(0.6) },
                    { threshold: 0,      color: Cesium.Color.fromCssColorString('#F0E442').withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 50, color: Cesium.Color.fromCssColorString('#CC79A7').withAlpha(0.8) },
                    { threshold: 30, color: Cesium.Color.fromCssColorString('#0072B2').withAlpha(0.8) },
                    { threshold: 10, color: Cesium.Color.fromCssColorString('#009E73').withAlpha(0.8) },
                    { threshold: 0,  color: Cesium.Color.fromCssColorString('#D55E00').withAlpha(0.8) }
                ]
            },
            'Colorblind-Friendly (Protan)': {
                name: 'Colorblind-Friendly (Protan)',
                description: 'Accessible palette for protanomaly',
                colors: [
                    { threshold: 500000, color: Cesium.Color.fromCssColorString('#117733').withAlpha(0.6) },
                    { threshold: 100000, color: Cesium.Color.fromCssColorString('#332288').withAlpha(0.6) },
                    { threshold: 50000,  color: Cesium.Color.fromCssColorString('#44AA99').withAlpha(0.6) },
                    { threshold: 10000,  color: Cesium.Color.fromCssColorString('#88CCEE').withAlpha(0.6) },
                    { threshold: 0,      color: Cesium.Color.fromCssColorString('#DDCC77').withAlpha(0.6) }
                ],
                craterColors: [
                    { threshold: 50, color: Cesium.Color.fromCssColorString('#117733').withAlpha(0.8) },
                    { threshold: 30, color: Cesium.Color.fromCssColorString('#332288').withAlpha(0.8) },
                    { threshold: 10, color: Cesium.Color.fromCssColorString('#44AA99').withAlpha(0.8) },
                    { threshold: 0,  color: Cesium.Color.fromCssColorString('#88CCEE').withAlpha(0.8) }
                ]
            }
        };

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
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    allMeteorites = data;
                    populateMeteoriteClassOptions();
                    initializeMeteoriteSliders();
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

            filteredCraters = allCraters.filter(feature => {
                const properties = feature.properties;
                let diameter = parseFloat(properties['Crater diamter [km]']) || 0;
                let age_min = properties.age_min !== null ? parseFloat(properties.age_min) : 0;
                let age_max = properties.age_max !== null ? parseFloat(properties.age_max) : 2500;
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
                    const pointSize = mass !== 'Unknown' ? Math.min(Math.max(mass / 10000, 5), 20) : 5;
                    const entity = meteoriteDataSource.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: pointSize,
                            color: mass !== 'Unknown' ? getMeteoriteColor(mass) : Cesium.Color.GRAY.withAlpha(0.6)
                        },
                        properties: {
                            isMeteorite: true,
                            meteoriteIndex: index
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

                if (geometry && geometry.type === "Point") {
                    const [lon, lat] = geometry.coordinates;
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
                }
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
            if (diameter >= 300) return 25;
            if (diameter >= 200) return 22;
            if (diameter >= 100) return 18;
            if (diameter >= 50) return 14;
            if (diameter >= 10) return 10;
            return 7;
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
                    orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(-90) }
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
                orientation: { heading: Cesium.Math.toRadians(270), pitch: Cesium.Math.toRadians(-90) }
            });
        }

        function openModal() {
            updateModalTable();
            document.getElementById('modal').style.display = 'block';
        }

        function openCraterModal() {
            updateCraterModalTable();
            document.getElementById('craterModal').style.display = 'block';
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
                tbody.innerHTML = '<tr><td colspan="5">No meteorite data available.</td></tr>';
                return;
            }
            const searchQuery = document.getElementById('meteoriteSearchInput').value.toLowerCase();
            tbody.innerHTML = '';
            filteredMeteorites.forEach((meteorite, index) => {
                const name = meteorite.name || 'Unknown';
                if (name.toLowerCase().includes(searchQuery)) {
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                    const massDisplay = formatMass(mass);
                    const recclass = meteorite.recclass || 'Unknown';
                    const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                    const fall = meteorite.fall || 'Unknown';
                    const tr = document.createElement('tr');
                    tr.style.cursor = 'pointer';
                    tr.onclick = () => flyToMeteorite(index);
                    tr.innerHTML = `
                        <td>${name}</td>
                        <td>${massDisplay}</td>
                        <td>${recclass}</td>
                        <td>${year}</td>
                        <td>${fall}</td>
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
                tbody.innerHTML = '<tr><td colspan="7">No crater data available.</td></tr>';
                return;
            }
            const searchQuery = document.getElementById('craterSearchInput').value.toLowerCase();
            tbody.innerHTML = '';
            headerRow.innerHTML = '';

            // Populate table headers
            craterPropertyNames.forEach((propName, index) => {
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
                    tr.onclick = () => flyToCrater(index);
                    craterPropertyNames.forEach(propName => {
                        const td = document.createElement('td');
                        const value = properties[propName] !== undefined ? properties[propName] : 'Unknown';
                        td.innerText = value;
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

            const minDiameter = Math.min(...diameters);
            const maxDiameter = Math.max(...diameters);
            const minAge = Math.min(...ages);
            const maxAge = Math.max(...ages);

            // Define the slider's maximum diameter limit
            const sliderMaxDiameter = 280;

            // Set diameter sliders with manual upper limit
            const diameterRangeMin = document.getElementById('diameterRangeMin');
            const diameterRangeMax = document.getElementById('diameterRangeMax');

            diameterRangeMin.min = minDiameter;
            diameterRangeMin.max = sliderMaxDiameter;
            diameterRangeMin.value = minDiameter;

            diameterRangeMax.min = minDiameter;
            diameterRangeMax.max = sliderMaxDiameter;
            diameterRangeMax.value = sliderMaxDiameter;

            // Set age sliders
            const ageRangeMin = document.getElementById('ageRangeMin');
            const ageRangeMax = document.getElementById('ageRangeMax');

            ageRangeMin.min = minAge;
            ageRangeMin.max = maxAge;
            ageRangeMin.value = minAge;

            ageRangeMax.min = minAge;
            ageRangeMax.max = maxAge;
            ageRangeMax.value = maxAge;

            updateCraterSlidersDisplay();
        }
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
        document.getElementById('meteoriteClassSelect').addEventListener('change', () => {
            applyFilters();
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
            document.getElementById('ageRangeValue').innerText = `${ageMin.toFixed(2)} - ${ageMax.toFixed(2)} Ma`;
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
            applyFilters();
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
            if (diameter >= 200) return 20;
            if (diameter >= 100) return 15;
            if (diameter >= 50) return 10;
            return 7;
        }

        // In initializeCraterSliders, ensure maxDiameter is used in various places
        function initializeCraterSliders() {
            const diameters = allCraters.map(c => c.properties['Crater diamter [km]'] ? parseFloat(c.properties['Crater diamter [km]']) : null).filter(d => d !== null);
            const ages = allCraters.map(c => c.properties.age_min !== null ? parseFloat(c.properties.age_min) : null).filter(a => a !== null);

            const minDiameter = Math.min(...diameters);
            const maxDiameter = Math.max(...diameters);
            const minAge = Math.min(...ages);
            const maxAge = Math.max(...ages);

            document.getElementById('diameterRangeMin').min = minDiameter;
            document.getElementById('diameterRangeMin').max = maxDiameter;
            document.getElementById('diameterRangeMax').min = minDiameter;
            document.getElementById('diameterRangeMax').max = maxDiameter;
            document.getElementById('diameterRangeMin').value = minDiameter;
            document.getElementById('diameterRangeMax').value = maxDiameter;

            document.getElementById('ageRangeMin').min = minAge;
            document.getElementById('ageRangeMin').max = maxAge;
            document.getElementById('ageRangeMax').min = minAge;
            document.getElementById('ageRangeMax').max = maxAge;
            document.getElementById('ageRangeMin').value = minAge;
            document.getElementById('ageRangeMax').value = maxAge;

            updateCraterSlidersDisplay();
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

        window.flyToMeteorite = flyToMeteorite;
        window.flyToCrater = flyToCrater;

        const optionsButton = document.getElementById('optionsButton');
        const controls = document.getElementById('controls');
        const closeOptions = document.getElementById('closeOptions');

        optionsButton.onclick = () => {
            if (controls.style.display === 'none' || controls.style.display === '') {
                closeOtherMenus('options');
                controls.style.display = 'block';
            } else {
                controls.style.display = 'none';
            }
        };

        closeOptions.onclick = () => {
            controls.style.display = 'none';
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

            scheme.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `<span class="legend-icon" style="background-color: ${item.color.toCssColorString()};"></span>`;
                let label = '';
                if (item.threshold === 0) {
                    label = `Diameter < ${scheme.find(s => s.threshold > 0).threshold} km`;
                } else {
                    label = `Diameter ≥ ${item.threshold} km`;
                }
                li.innerHTML += label;
                list.appendChild(li);
            });
        }

        function updateMeteoriteLegend() {
            const legendContainer = document.getElementById('meteoriteLegend');
            legendContainer.innerHTML = '<h3>🌠 Meteorites</h3><ul class="legend-list"></ul>';
            const list = legendContainer.querySelector('.legend-list');
            const selectedScheme = document.getElementById('meteoriteColorScheme').value;
            const scheme = colorSchemes[selectedScheme].colors;

            scheme.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `<span class="legend-icon" style="background-color: ${item.color.toCssColorString()};"></span>`;
                let label = '';
                if (item.threshold === 0) {
                    label = `Mass < ${scheme.find(s => s.threshold > 0).threshold}g`;
                } else {
                    label = `Mass ≥ ${item.threshold.toLocaleString()}g`;
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
