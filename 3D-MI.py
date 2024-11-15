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
        /* General styles */
        html, body, #cesiumContainer {
            width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #header {
            position: absolute;
            top: 10px;
            left: 10px;
            right: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1;
        }
        #header h1 {
            margin: 0;
            font-size: 24px;
            color: white;
            text-shadow: 1px 1px 2px black;
        }
        #header-buttons {
            display: flex;
            gap: 10px;
        }
        #header-buttons button {
            background: rgba(0, 0, 0, 0.7);
            color: white;
            border: none;
            padding: 10px;
            cursor: pointer;
            border-radius: 5px;
        }
        #header-buttons button:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        /* Controls, modals, bars, tooltips styles */
        /* ... (Same as before with adjustments for new buttons and elements) */
        #controls, #keyContainer {
            /* Adjust styles accordingly */
            max-height: calc(100% - 120px);
            overflow-y: auto;
            display: none;
            width: 300px;
        }
        #controls {
            top: 100px;
        }
        #keyContainer {
            top: 150px;
        }
        /* Legend styles */
        #legend {
            margin-top: 10px;
        }
        #legend div {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        #legend span {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 10px;
        }
        /* Search input styles in modals */
        .modal-search {
            margin-bottom: 10px;
            width: 100%;
            box-sizing: border-box;
            padding: 5px;
            font-size: 16px;
        }
        /* Adjust other styles to accommodate new elements */
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <div id="header">
        <h1>🌠 Global Meteorite Specimens & Impact Craters 🌠</h1>
        <div id="header-buttons">
            <button id="optionsButton" title="Options">⚙️</button>
            <button id="keyButton" title="Legend">🗺️</button>
            <button id="infoButton" title="Information">ℹ️</button>
        </div>
    </div>
    <!-- Controls Panel -->
    <div id="controls">
        <!-- Close button and content -->
        <!-- ... (Same as before) -->
    </div>
    <!-- Key (Legend) Panel -->
    <div id="keyContainer">
        <button class="close-button" id="closeKey">&times;</button>
        <h3>Legend</h3>
        <div id="legend">
            <h4>Meteorite Mass (g):</h4>
            <div>
                <span style="background-color: #800080;"></span> < 10,000
            </div>
            <div>
                <span style="background-color: #FF0000;"></span> 10,000 - 50,000
            </div>
            <div>
                <span style="background-color: #FFA500;"></span> 50,000 - 100,000
            </div>
            <div>
                <span style="background-color: #FFFF00;"></span> > 100,000
            </div>
            <h4>Impact Crater Diameter (km):</h4>
            <div>
                <span style="background-color: #ADD8E6;"></span> < 10
            </div>
            <div>
                <span style="background-color: #0000FF;"></span> 10 - 30
            </div>
            <div>
                <span style="background-color: #00008B;"></span> 30 - 50
            </div>
            <div>
                <span style="background-color: #000080;"></span> > 50
            </div>
        </div>
    </div>
    <!-- Other modals and elements -->
    <!-- ... (Same as before with search inputs added to modals) -->
    <!-- Meteorite Modal -->
    <div id="modal">
        <div id="modal-content">
            <span id="closeModal">&times;</span>
            <h2>All Meteorites</h2>
            <input type="text" id="modalMeteoriteSearch" class="modal-search" placeholder="Search meteorites...">
            <table id="fullMeteoriteTable">
                <!-- ... (Same as before) -->
            </table>
        </div>
    </div>
    <!-- Crater Modal -->
    <div id="craterModal">
        <div id="craterModal-content">
            <span id="closeCraterModal">&times;</span>
            <h2>All Impact Craters</h2>
            <input type="text" id="modalCraterSearch" class="modal-search" placeholder="Search impact craters...">
            <table id="fullCraterTable">
                <!-- ... (Same as before) -->
            </table>
        </div>
    </div>
    <!-- Tooltip and scripts -->
    <div id="tooltip"></div>
    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            // ... (Same as before)
            sceneModePicker: true,
            animation: false,
            timeline: false
        });

        let allMeteorites = [];
        let filteredMeteorites = [];
        const impactCraters = {{ impact_craters | tojson }};
        let filteredCraters = impactCraters.features;
        const allCraters = impactCraters.features;

        // Clustering
        viewer.scene.globe.depthTestAgainstTerrain = true;
        const meteoriteDataSource = new Cesium.CustomDataSource('meteorites');
        viewer.dataSources.add(meteoriteDataSource);

        const craterDataSource = new Cesium.CustomDataSource('craters');
        viewer.dataSources.add(craterDataSource);

        // Color scales
        function getMeteoriteColor(mass) {
            if (mass >= 100000) return Cesium.Color.YELLOW.withAlpha(0.6);
            if (mass >= 50000)  return Cesium.Color.ORANGE.withAlpha(0.6);
            if (mass >= 10000)  return Cesium.Color.RED.withAlpha(0.6);
            return Cesium.Color.PURPLE.withAlpha(0.6);
        }

        function getCraterColor(diameter) {
            if (diameter >= 50) return Cesium.Color.NAVY.withAlpha(0.8);
            if (diameter >= 30) return Cesium.Color.DARKBLUE.withAlpha(0.8);
            if (diameter >= 10) return Cesium.Color.BLUE.withAlpha(0.8);
            return Cesium.Color.LIGHTBLUE.withAlpha(0.8);
        }

        // Fetch meteorite data and apply filters
        function fetchAllMeteorites() {
            // ... (Same as before)
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
            // ... (Same as before)
            // Filter meteorites
            filteredMeteorites = allMeteorites.filter(m => {
                // ... (Same as before)
                // Apply filters
                return yearMatch && massMatch;
            });

            // Filter craters
            filteredCraters = allCraters.filter(feature => {
                // ... (Same as before)
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

        function updateMeteoriteData() {
            // ... (Same as before with clustering fixed)
            meteoriteDataSource.entities.removeAll();

            filteredMeteorites.forEach((meteorite, index) => {
                // ... (Calculate positions and properties)
                if (lat !== undefined && lon !== undefined && !isNaN(lat) && !isNaN(lon)) {
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                    const entity = meteoriteDataSource.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 10000, 5), 20) : 5,
                            color: mass !== 'Unknown' ? getMeteoriteColor(mass) : Cesium.Color.GRAY.withAlpha(0.6),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        properties: {
                            isMeteorite: true,
                            meteoriteIndex: index
                        }
                    });
                }
            });

            meteoriteDataSource.clustering.enabled = document.getElementById('clusterMeteorites').checked;
            meteoriteDataSource.clustering.pixelRange = 50;
            meteoriteDataSource.clustering.minimumClusterSize = 5;
            meteoriteDataSource.clustering.clusterPoints = true;
        }

        function updateCraterData() {
            // ... (Same as before)
            craterDataSource.entities.removeAll();

            filteredCraters.forEach((feature, index) => {
                // ... (Calculate properties)
                craterDataSource.entities.add({
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
            });
        }

        // Functions to update modals, tooltips, search functionality
        // ... (Include search functionality in modals)
        function addModalSearchFunctionality() {
            document.getElementById('modalMeteoriteSearch').addEventListener('input', function() {
                updateModalTable(this.value.toLowerCase());
            });

            document.getElementById('modalCraterSearch').addEventListener('input', function() {
                updateCraterModalTable(this.value.toLowerCase());
            });
        }

        function updateModalTable(searchTerm = '') {
            // ... (Update table based on searchTerm)
            const tbody = document.querySelector('#fullMeteoriteTable tbody');
            const filtered = filteredMeteorites.filter(meteorite => {
                return meteorite.name && meteorite.name.toLowerCase().includes(searchTerm);
            });
            tbody.innerHTML = filtered.map((meteorite, index) => {
                // ... (Same as before)
            }).join('');
        }

        function updateCraterModalTable(searchTerm = '') {
            // ... (Update table based on searchTerm)
            const tbody = document.querySelector('#fullCraterTable tbody');
            const filtered = filteredCraters.filter(crater => {
                return crater.properties.crater_name && crater.properties.crater_name.toLowerCase().includes(searchTerm);
            });
            tbody.innerHTML = filtered.map((crater, index) => {
                // ... (Same as before)
            }).join('');
        }

        // Fix sortTable function
        function sortTable(tableId, colIndex) {
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const dir = tbody.getAttribute('data-sort-dir') === 'asc' ? 'desc' : 'asc';
            tbody.setAttribute('data-sort-dir', dir);

            rows.sort((a, b) => {
                const x = a.getElementsByTagName('TD')[colIndex].innerText.toLowerCase();
                const y = b.getElementsByTagName('TD')[colIndex].innerText.toLowerCase();

                if (!isNaN(parseFloat(x)) && !isNaN(parseFloat(y))) {
                    return dir === 'asc' ? parseFloat(x) - parseFloat(y) : parseFloat(y) - parseFloat(x);
                } else {
                    if (x < y) return dir === 'asc' ? -1 : 1;
                    if (x > y) return dir === 'asc' ? 1 : -1;
                    return 0;
                }
            });

            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        }

        // Adjust UI buttons and add event listeners
        document.getElementById('keyButton').onclick = () => {
            const keyContainer = document.getElementById('keyContainer');
            keyContainer.style.display = keyContainer.style.display === 'block' ? 'none' : 'block';
        };
        document.getElementById('closeKey').onclick = () => {
            document.getElementById('keyContainer').style.display = 'none';
        };

        // Initialize application
        function initialize() {
            fetchAllMeteorites();
            applyFilters();
            addModalSearchFunctionality();
            initializeEventListeners();
        }

        function initializeEventListeners() {
            // Attach event listeners for buttons and inputs
            // ... (Same as before)
        }

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
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
