import os
from flask import Flask, render_template_string

# Define Flask app
app = Flask(__name__)

# Retrieve the Cesium Ion Access Token from environment variables
CESIUM_ION_ACCESS_TOKEN = os.environ.get('CESIUM_ION_ACCESS_TOKEN')

# Ensure the Cesium Ion Access Token is available
if not CESIUM_ION_ACCESS_TOKEN:
    raise ValueError("CESIUM_ION_ACCESS_TOKEN environment variable is not set.")

# HTML template with Cesium-based functionality for meteorite impacts
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
            background-color: #f5f5f5;
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
        #controls input {
            padding: 5px;
            font-size: 14px;
            margin-right: 10px;
            width: 80px;
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
            #controls label, #controls input, #controls button, #controls select {
                width: 100%;
                text-align: center;
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
            <div>
                <label for="minYear">Min Year:</label>
                <input type="number" id="minYear" placeholder="1900">
                <label for="maxYear">Max Year:</label>
                <input type="number" id="maxYear" placeholder="2020">
            </div>
            <div>
                <label for="minMass">Min Mass (g):</label>
                <input type="number" id="minMass" placeholder="0">
                <label for="maxMass">Max Mass (g):</label>
                <input type="number" id="maxMass" placeholder="100000">
            </div>
            <button id="applyFilters">Apply Filters</button>
        </div>
    </div>

    <!-- Tooltip -->
    <div id="tooltip"></div>

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

        let meteorites = [];
        let allMeteorites = [];

        // Function to fetch meteorites from NASA API
        function fetchMeteorites() {
            const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=50000';

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    allMeteorites = data;
                    updateMeteoriteData();
                })
                .catch(error => {
                    console.error('Error fetching meteorite data:', error);
                });
        }

        // Function to update meteorite data on the map
        function updateMeteoriteData() {
            // Remove existing entities
            viewer.entities.removeAll();

            // Apply filters
            const minYear = parseInt(document.getElementById('minYear').value);
            const maxYear = parseInt(document.getElementById('maxYear').value);
            const minMass = parseInt(document.getElementById('minMass').value);
            const maxMass = parseInt(document.getElementById('maxMass').value);

            meteorites = allMeteorites.filter(meteorite => {
                // Check for valid geolocation
                if (!meteorite.geolocation || !meteorite.geolocation.coordinates) {
                    return false;
                }
                
                // Filter by year
                let year = meteorite.year ? new Date(meteorite.year).getFullYear() : null;
                if (year) {
                    if (minYear && year < minYear) return false;
                    if (maxYear && year > maxYear) return false;
                } else {
                    return false; // Exclude if year is not available
                }

                // Filter by mass
                let mass = meteorite.mass ? parseFloat(meteorite.mass) : null;
                if (mass !== null) {
                    if (!isNaN(minMass) && minMass !== 0 && mass < minMass) return false;
                    if (!isNaN(maxMass) && mass > maxMass) return false;
                } else {
                    return false; // Exclude if mass is not available
                }

                return true;
            });

            // Add meteorites to the map
            meteorites.forEach(meteorite => {
                const [lon, lat] = meteorite.geolocation.coordinates;
                const name = meteorite.name || 'Unknown';
                const mass = meteorite.mass ? Number(meteorite.mass) : 'Unknown';
                const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';
                const recclass = meteorite.recclass || 'Unknown';

                viewer.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(lon, lat),
                    point: {
                        pixelSize: mass !== 'Unknown' ? Math.min(Math.max(mass / 1000, 5), 25) : 10,
                        color: Cesium.Color.CYAN.withAlpha(0.6),
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 1
                    },
                    description: `
                        <b>Name:</b> ${name}<br>
                        <b>Mass:</b> ${mass !== 'Unknown' ? mass + ' g' : 'Unknown'}<br>
                        <b>Class:</b> ${recclass}<br>
                        <b>Year:</b> ${year}
                    `
                });
            });

            if (viewer.entities.values.length > 0) {
                viewer.zoomTo(viewer.entities).otherwise(() => {
                    console.log('Zoom failed');
                });
            }
        }

        // Event listener for 'Apply Filters' button
        document.getElementById('applyFilters').addEventListener('click', function() {
            updateMeteoriteData();
        });

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

        // Fetch initial meteorite data
        fetchMeteorites();
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
    app.run(host='0.0.0.0', port=5000)
