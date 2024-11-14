import os
from flask import Flask, render_template_string

# Define Flask app
app = Flask(__name__)

# Retrieve the Cesium Ion Access Token from environment variables
CESIUM_ION_ACCESS_TOKEN = os.environ.get('CESIUM_ION_ACCESS_TOKEN')

# Ensure the Cesium Ion Access Token is available
if not CESIUM_ION_ACCESS_TOKEN:
    raise ValueError("CESIUM_ION_ACCESS_TOKEN environment variable is not set.")

# HTML template with Cesium-based meteorite impacts visualization and enhanced features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🌠 Global Meteorite Impacts Visualization</title>
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
        }
        #controls label {
            font-size: 14px;
            color: #333;
        }
        #yearRangeContainer,
        #massRangeContainer,
        #fallFindContainer,
        #typeContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        #yearRange,
        #massRange {
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
        /* Legend Styling */
        #legend {
            margin-top: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 12px;
            color: #333;
        }
        .legend-color {
            width: 15px;
            height: 15px;
            margin-right: 5px;
            border: 1px solid #000;
        }
        /* Tooltip Styling */
        #tooltip {
            position: absolute;
            background: rgba(50, 50, 50, 0.9);
            color: #fff;
            padding: 8px;
            border-radius: 4px;
            pointer-events: none;
            z-index: 5;
            display: none;
            max-width: 200px;
            font-size: 12px;
        }
        /* Modal Styling */
        #modal {
            display: none;
            position: fixed;
            z-index: 10;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.5);
        }
        #modalContent {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            max-height: 80%;
            overflow-y: auto;
            border-radius: 8px;
        }
        #closeModal {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        #closeModal:hover,
        #closeModal:focus {
            color: black;
            text-decoration: none;
        }
        #fullMeteoriteTable {
            width: 100%;
            border-collapse: collapse;
        }
        #fullMeteoriteTable th, #fullMeteoriteTable td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        #fullMeteoriteTable th {
            background-color: #f2f2f2;
        }
        #fullMeteoriteTable tr:hover {
            background-color: #ddd;
        }
        /* Search Box Styling */
        #searchBox {
            position: absolute;
            top: 15px;
            right: 30px;
            z-index: 4;
            display: flex;
            align-items: center;
        }
        #searchInput {
            padding: 6px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-radius: 4px 0 0 4px;
            outline: none;
        }
        #searchButton {
            padding: 6px 10px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-left: none;
            border-radius: 0 4px 4px 0;
            background-color: #0078D7;
            color: #fff;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        #searchButton:hover {
            background-color: #005a9e;
        }
        /* Meteorite Bar Styling */
        #meteoriteBar {
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 3;
            display: flex;
            align-items: center;
            gap: 15px;
            max-width: 90%;
            overflow-x: auto;
        }
        .bar-item {
            font-size: 14px;
            color: #333;
            cursor: pointer;
            white-space: nowrap;
        }
        .bar-item:hover {
            text-decoration: underline;
        }
        /* Responsive Design */
        @media (max-width: 768px) {
            #controls {
                flex-direction: column;
            }
            #searchBox {
                top: auto;
                bottom: 60px;
            }
            #meteoriteBar {
                bottom: 70px;
            }
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>

    <!-- Header with title, description, and controls -->
    <div id="header">
        <h1>🌠 Global Meteorite Impacts Visualization</h1>
        <p>Explore meteorite landing sites around the world in an interactive 3D map.</p>
        <div id="controls">
            <div id="yearRangeContainer">
                <label for="yearRange">Year Range: <span id="yearRangeValue">All</span></label>
                <input type="range" id="yearRange" min="860" max="2023" value="2023" step="1">
            </div>
            <div id="massRangeContainer">
                <label for="massRange">Max Mass (g): <span id="massRangeValue">All</span></label>
                <input type="range" id="massRange" min="0" max="100000" value="100000" step="1000">
            </div>
            <div id="fallFindContainer">
                <label for="fallFindSelect">Type:</label>
                <select id="fallFindSelect">
                    <option value="All">All</option>
                    <option value="Fell">Fell</option>
                    <option value="Found">Found</option>
                </select>
            </div>
            <div id="typeContainer">
                <label for="meteoriteTypeSelect">Meteorite Class:</label>
                <select id="meteoriteTypeSelect">
                    <option value="All">All</option>
                    <!-- Options will be populated dynamically -->
                </select>
            </div>
            <select id="basemapSelector">
                <option value="Cesium World Imagery">Cesium World Imagery (Default)</option>
                <option value="OpenStreetMap">OpenStreetMap</option>
            </select>
        </div>
        <!-- Legend and other elements -->
        <div id="legend">
            <!-- Dynamic Legend Items -->
        </div>
    </div>

    <!-- Top meteorites bar -->
    <div id="meteoriteBar">
        <!-- Populated dynamically -->
    </div>

    <!-- Search box -->
    <div id="searchBox">
        <input type="text" id="searchInput" placeholder="Search location...">
        <button id="searchButton">🔍</button>
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
        let meteorites = [];

        // Define current mass ranges for legend
        let currentMassRanges = [];

        // Function to get color based on mass
        function getColor(mass, ranges) {
            for (let i = 0; i < ranges.length; i++) {
                if (mass >= ranges[i].min && mass < ranges[i].max) {
                    return Cesium.Color.fromCssColorString(ranges[i].color).withAlpha(0.6);
                }
            }
            return Cesium.Color.GRAY.withAlpha(0.6);
        }

        // Fetch all meteorites from NASA API
        function fetchMeteorites() {
            let url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=10000';

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (!data) throw new Error('Invalid meteorite data format.');
                    allMeteorites = data;
                    populateMeteoriteTypes();
                    applyFilters();
                })
                .catch(error => {
                    console.error('Error fetching meteorite data:', error);
                });
        }

        // Populate Meteorite Type dropdown
        function populateMeteoriteTypes() {
            const typeSelect = document.getElementById('meteoriteTypeSelect');
            const types = new Set();
            allMeteorites.forEach(meteorite => {
                const recclass = meteorite.recclass || 'Unknown';
                types.add(recclass);
            });

            // Clear existing options except 'All'
            typeSelect.innerHTML = '<option value="All">All</option>';

            // Sort types alphabetically
            const sortedTypes = Array.from(types).sort();

            sortedTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeSelect.appendChild(option);
            });
        }

        function applyFilters() {
            const yearFilter = parseInt(document.getElementById('yearRange').value);
            const massFilter = parseInt(document.getElementById('massRange').value);
            const fallFindFilter = document.getElementById('fallFindSelect').value;
            const typeFilter = document.getElementById('meteoriteTypeSelect').value;

            // Update legend before filtering
            updateLegend(massFilter);

            // Filter data
            meteorites = allMeteorites.filter(meteorite => {
                const mass = meteorite.mass ? parseFloat(meteorite.mass) : 0;
                const year = meteorite.year ? new Date(meteorite.year).getFullYear() : null;
                const fallFind = meteorite.fall || 'Unknown';
                const recclass = meteorite.recclass || 'Unknown';

                let passYear = true;
                let passMass = true;
                let passFallFind = true;
                let passType = true;

                if (yearFilter !== 2023 && year) {
                    passYear = year <= yearFilter;
                }

                if (massFilter !== 100000) {
                    passMass = mass <= massFilter;
                }

                if (fallFindFilter !== 'All') {
                    passFallFind = fallFind === fallFindFilter;
                }

                if (typeFilter !== 'All') {
                    passType = recclass === typeFilter;
                }

                return passYear && passMass && passFallFind && passType;
            });

            updateMeteoriteData();
        }

        // Update meteorite data on the map and top list
        function updateMeteoriteData() {
            const sortedMeteorites = meteorites.filter(m => m.mass).sort((a, b) => parseFloat(b.mass) - parseFloat(a.mass));
            const top10 = sortedMeteorites.slice(0, 10);
            const bar = document.getElementById('meteoriteBar');
            bar.innerHTML = '<div class="bar-item"><strong>Top Meteorites:</strong></div>';

            top10.forEach((meteorite, index) => {
                const name = meteorite.name || 'Unknown';
                const mass = meteorite.mass ? parseFloat(meteorite.mass) : 0;
                const massDisplay = mass > 500 ? (mass / 1000).toFixed(2) + ' kg' : mass + ' g';
                const div = document.createElement('div');
                div.className = 'bar-item';
                div.innerText = `🌠 ${name} - ${massDisplay}`;
                div.onclick = () => flyToMeteorite(meteorites.indexOf(meteorite));
                bar.appendChild(div);
            });

            const viewAll = document.createElement('div');
            viewAll.className = 'bar-item';
            viewAll.innerHTML = `<strong>View All</strong>`;
            viewAll.onclick = () => openModal();
            bar.appendChild(viewAll);

            // Remove existing entities
            viewer.entities.removeAll();

            addMeteoritePoints();
            if (viewer.entities.values.length > 0) {
                viewer.zoomTo(viewer.entities).otherwise(() => {
                    console.log('Zoom failed');
                });
            }
        }

        // Add meteorite points to the Cesium viewer
        function addMeteoritePoints() {
            meteorites.forEach((meteorite, index) => {
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
                    const recclass = meteorite.recclass || 'Unknown';
                    const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                    const fall = meteorite.fall || 'Unknown';

                    // Mass display logic
                    let massDisplay = 'Unknown';
                    if (mass !== 'Unknown') {
                        massDisplay = mass > 500 ? (mass / 1000).toFixed(2) + ' kg' : mass + ' g';
                    }

                    viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 1000, 5), 25) : 5,
                            color: mass !== 'Unknown' ? getColor(mass, currentMassRanges) : Cesium.Color.GRAY.withAlpha(0.6),
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
                        meteoriteIndex: index
                    });
                }
            });
        }

        // Update legend based on current mass selection
        function updateLegend(massFilter) {
            const legend = document.getElementById('legend');
            legend.innerHTML = '';

            // Define dynamic ranges based on mass filter
            // For simplicity, we'll divide the massFilter into 5 equal ranges
            const numRanges = 5;
            const rangeSize = massFilter / numRanges;
            currentMassRanges = [];

            for (let i = 0; i < numRanges; i++) {
                const min = i * rangeSize;
                const max = (i + 1) * rangeSize;
                const color = getColorForRange(i, numRanges);
                currentMassRanges.push({ min, max, color });
            }

            // Define the top range to include massFilter and above
            currentMassRanges.push({ min: massFilter, max: Infinity, color: '#FF0000' }); // Red for highest mass

            // Create legend items
            currentMassRanges.forEach(range => {
                let label;
                if (range.max === Infinity) {
                    label = `Mass ≥ ${formatMass(range.min)}`;
                } else {
                    label = `Mass ${formatMass(range.min)} - ${formatMass(range.max)}`;
                }

                const item = document.createElement('div');
                item.className = 'legend-item';
                item.innerHTML = `
                    <div class="legend-color" style="background-color: ${range.color};"></div>
                    <span>${label}</span>
                `;
                legend.appendChild(item);
            });
        }

        // Helper function to get color based on range index
        function getColorForRange(index, total) {
            const colors = ['cyan', 'green', 'yellow', 'orange', 'red'];
            return colors[index % colors.length];
        }

        // Helper function to format mass display
        function formatMass(mass) {
            return mass >= 1000 ? (mass / 1000).toFixed(2) + ' kg' : mass + ' g';
        }

        // Fly to a specific meteorite location
        function flyToMeteorite(index) {
            const meteorite = meteorites[index];
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
                    orientation: { pitch: Cesium.Math.toRadians(-30) }
                });
            }
        }

        // Tooltip functionality
        let tooltip = document.getElementById('tooltip');

        viewer.screenSpaceEventHandler.setInputAction(function onMouseMove(movement) {
            const pickedObject = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(pickedObject) && pickedObject.id) {
                const description = pickedObject.id.description.getValue();
                tooltip.style.display = 'block';
                tooltip.innerHTML = description.replace(/<br>/g, '\n').replace(/<[^>]+>/g, '');
                let position = movement.endPosition;
                tooltip.style.left = position.x + 15 + 'px';
                tooltip.style.top = position.y + 15 + 'px';
            } else {
                tooltip.style.display = 'none';
            }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

        // Modal functionality for viewing all meteorites
        function openModal() {
            const modal = document.getElementById('modal');
            const tbody = document.querySelector('#fullMeteoriteTable tbody');
            if (!meteorites.length) {
                tbody.innerHTML = '<tr><td colspan="5">No meteorite data available.</td></tr>';
                return;
            }
            tbody.innerHTML = meteorites.map((meteorite, index) => {
                const name = meteorite.name || 'Unknown';
                const mass = meteorite.mass ? parseFloat(meteorite.mass) : 0;
                const massDisplay = mass > 500 ? (mass / 1000).toFixed(2) + ' kg' : mass + ' g';
                const recclass = meteorite.recclass || 'Unknown';
                const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                const fall = meteorite.fall || 'Unknown';
                return `
                    <tr onclick="flyToMeteorite(${index})" style="cursor:pointer;">
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

        // Close modal when clicking on <span> (x)
        document.getElementById('closeModal').onclick = function() {
            document.getElementById('modal').style.display = 'none';
        }

        // Ensure flyToMeteorite is accessible globally
        window.flyToMeteorite = flyToMeteorite;

        // Search location functionality
        document.getElementById('searchButton').addEventListener('click', function() {
            const query = document.getElementById('searchInput').value;
            if (!query.trim()) return;

            const geocoder = new Cesium.Geocoder(viewer.scene, {
                url: 'https://nominatim.openstreetmap.org/search?format=json&q='
            });

            geocoder.geocode(query).then(results => {
                if (results.length > 0) {
                    const result = results[0];
                    viewer.camera.flyTo({
                        destination: Cesium.Cartesian3.fromDegrees(result.lon, result.lat, 200000),
                        duration: 2,
                        orientation: { pitch: Cesium.Math.toRadians(-30) }
                    });
                } else {
                    alert('Location not found.');
                }
            });
        });

        // Basemap selector functionality
        document.getElementById('basemapSelector').addEventListener('change', function() {
            const selected = this.value;
            viewer.imageryLayers.removeAll();
            if (selected === 'Cesium World Imagery') {
                viewer.imageryLayers.addImageryProvider(new Cesium.IonImageryProvider({ assetId: 2 }));
            } else if (selected === 'OpenStreetMap') {
                viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({
                    url: 'https://a.tile.openstreetmap.org/'
                }));
            }
        });

        // Event listeners for filters
        document.getElementById('yearRange').addEventListener('input', function() {
            const year = parseInt(this.value);
            document.getElementById('yearRangeValue').innerText = year === 2023 ? 'All' : year;
            applyFilters();
        });

        document.getElementById('massRange').addEventListener('input', function() {
            const mass = parseInt(this.value);
            document.getElementById('massRangeValue').innerText = mass === 100000 ? 'All' : mass + ' g';
            applyFilters();
        });

        document.getElementById('fallFindSelect').addEventListener('change', function() {
            applyFilters();
        });

        document.getElementById('meteoriteTypeSelect').addEventListener('change', function() {
            applyFilters();
        });

        // Fetch meteorite data on load
        window.onload = function() {
            fetchMeteorites();
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        cesium_token=CESIUM_ION_ACCESS_TOKEN
    )

if __name__ == '__main__':
    # Use the port provided by Railway or default to 8080
    port = int(os.environ.get('PORT', 8080))
    # Bind to all network interfaces and use the specified port
    app.run(debug=False, host='0.0.0.0', port=port)
