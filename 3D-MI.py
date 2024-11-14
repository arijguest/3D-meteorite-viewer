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
        #yearRangeContainer {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        #yearRange {
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
            background: rgba(255,255,255,0.9);
            padding: 10px 15px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 3px;
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
        #modal {
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
        #modalContent {
            background-color: #fff;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 90%;
            max-width: 800px;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
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
            top: 15px;
            right: 30px;
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
                top: 10px;
                right: 20px;
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
            <button id="toggleHeatmap">Enable Heatmap</button>
            <select id="basemapSelector">
                <option value="Cesium World Imagery">Cesium World Imagery (Default)</option>
                <option value="OpenStreetMap">OpenStreetMap</option>
            </select>
        </div>
        <div id="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: cyan;"></div>
                <span>Mass &lt; 1,000g</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: green;"></div>
                <span>1,000g ≤ Mass &lt; 10,000g</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: yellow;"></div>
                <span>10,000g ≤ Mass &lt; 50,000g</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: orange;"></div>
                <span>50,000g ≤ Mass &lt; 100,000g</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: red;"></div>
                <span>Mass ≥ 100,000g</span>
            </div>
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
                        <th>Mass (g)</th>
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

        let heatmapEnabled = false;
        let meteorites = [];
        let heatmapPoints = [];

        // Function to get color based on mass
        function getColor(mass) {
            if (mass >= 100000) return Cesium.Color.RED.withAlpha(0.6);
            if (mass >= 50000)  return Cesium.Color.ORANGE.withAlpha(0.6);
            if (mass >= 10000)  return Cesium.Color.YELLOW.withAlpha(0.6);
            if (mass >= 1000)   return Cesium.Color.GREEN.withAlpha(0.6);
            return Cesium.Color.CYAN.withAlpha(0.6);
        }

        // Fetch meteorites from NASA API based on selected year range
        function fetchMeteorites(year) {
            let url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=1000';
            if (year !== 'All') {
                url += `&$where=year >= '${year}-01-01T00:00:00.000'`;
            }

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (!data) throw new Error('Invalid meteorite data format.');
                    meteorites = data;
                    updateMeteoriteData();
                })
                .catch(error => {
                    console.error('Error fetching meteorite data:', error);
                });
        }

        // Update meteorite data on the map and top list
        function updateMeteoriteData() {
            const sortedMeteorites = meteorites.filter(m => m.mass).sort((a, b) => parseFloat(b.mass) - parseFloat(a.mass));
            const top10 = sortedMeteorites.slice(0, 10);
            const bar = document.getElementById('meteoriteBar');
            bar.innerHTML = '<div class="bar-item"><strong>Top Meteorites:</strong></div>';

            top10.forEach((meteorite, index) => {
                const name = meteorite.name || 'Unknown';
                const mass = parseFloat(meteorite.mass) || 0;
                const div = document.createElement('div');
                div.className = 'bar-item';
                div.innerText = `🌠 ${name} - ${mass}g`;
                div.onclick = () => flyToMeteorite(index);
                bar.appendChild(div);
            });

            const viewAll = document.createElement('div');
            viewAll.className = 'bar-item';
            viewAll.innerHTML = `<strong>View All</strong>`;
            viewAll.onclick = () => openModal();
            bar.appendChild(viewAll);

            // Remove existing entities
            viewer.entities.removeAll();
            heatmapPoints.forEach(pointCollection => {
                viewer.scene.primitives.remove(pointCollection);
            });
            heatmapPoints = [];

            if (heatmapEnabled) {
                addHeatmap();
            } else {
                addMeteoritePoints();
                if (viewer.entities.values.length > 0) {
                    viewer.zoomTo(viewer.entities).otherwise(() => {
                        console.log('Zoom failed');
                    });
                }
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

                    viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 1000, 5), 25) : 5,
                            color: mass !== 'Unknown' ? getColor(mass) : Cesium.Color.GRAY.withAlpha(0.6),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: `
                            <b>Name:</b> ${name}<br>
                            <b>ID:</b> ${id}<br>
                            <b>Latitude:</b> ${lat.toFixed(5)}<br>
                            <b>Longitude:</b> ${lon.toFixed(5)}<br>
                            <b>Mass:</b> ${mass} g<br>
                            <b>Class:</b> ${recclass}<br>
                            <b>Year:</b> ${year}<br>
                            <b>Fall/Find:</b> ${fall}
                        `,
                        meteoriteIndex: index
                    });
                }
            });
        }

        // Add heatmap using PointPrimitives
        function addHeatmap() {
            const pointCollection = new Cesium.PointPrimitiveCollection();
            viewer.scene.primitives.add(pointCollection);

            meteorites.forEach(meteorite => {
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
                    const mass = meteorite.mass ? parseFloat(meteorite.mass) : 0;

                    pointCollection.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        color: getColor(mass),
                        pixelSize: Math.max(5 + mass / 10000, 5)
                    });
                }
            });

            heatmapPoints.push(pointCollection);
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
        const tooltip = document.getElementById('tooltip');
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

        handler.setInputAction(movement => {
            const picked = viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(picked) && picked.id && picked.id.description) {
                tooltip.style.display = 'block';
                tooltip.innerHTML = picked.id.description.getValue();
                updateTooltipPosition(movement.endPosition);
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
            if (!meteorites.length) {
                tbody.innerHTML = '<tr><td colspan="5">No meteorite data available.</td></tr>';
                return;
            }
            tbody.innerHTML = meteorites.map((meteorite, index) => {
                const name = meteorite.name || 'Unknown';
                const mass = meteorite.mass ? parseFloat(meteorite.mass) : 'Unknown';
                const recclass = meteorite.recclass || 'Unknown';
                const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                const fall = meteorite.fall || 'Unknown';
                return `
                    <tr onclick='flyToMeteorite(${index})' style="cursor:pointer;">
                        <td>${name}</td>
                        <td>${mass}</td>
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
                            destination: Cesium.Cartesian3.fromDegrees(parseFloat(lon), parseFloat(lat), 2000000),
                            duration: 2,
                            orientation: { pitch: Cesium.Math.toRadians(-30) }
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

        // Event listeners for year range and heatmap toggle
        document.getElementById('yearRange').addEventListener('input', function() {
            const year = parseInt(this.value);
            document.getElementById('yearRangeValue').innerText = year === 2023 ? 'All' : year;
            fetchMeteorites(year === 2023 ? 'All' : year);
        });

        document.getElementById('toggleHeatmap').addEventListener('click', function() {
            heatmapEnabled = !heatmapEnabled;
            this.innerText = heatmapEnabled ? 'Disable Heatmap' : 'Enable Heatmap';
            updateMeteoriteData();
        });

        // Fetch initial meteorite data
        fetchMeteorites('All');

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
    # Use the port provided by Railway or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Bind to all network interfaces and use the specified port
    app.run(debug=False, host='0.0.0.0', port=port)
