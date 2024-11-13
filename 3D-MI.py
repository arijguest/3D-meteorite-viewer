import os
from flask import Flask, render_template_string

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
        }
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>

    <!-- Header with title and description -->
    <div id="header">
        <h1>🌠 Global Meteorite Impacts Visualization</h1>
        <p>Explore meteorite landing sites around the world in an interactive 3D map.</p>
    </div>

    <!-- Tooltip -->
    <div id="tooltip"></div>

    <!-- Script Section -->
    <script>
        Cesium.Ion.defaultAccessToken = '{{ cesium_token }}';
        const viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: true,
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

        // Function to determine color based on mass
        function getColor(mass) {
            if (mass >= 100000) return Cesium.Color.RED.withAlpha(0.6);
            if (mass >= 50000) return Cesium.Color.ORANGE.withAlpha(0.6);
            if (mass >= 10000) return Cesium.Color.YELLOW.withAlpha(0.6);
            if (mass >= 1000) return Cesium.Color.GREEN.withAlpha(0.6);
            return Cesium.Color.CYAN.withAlpha(0.6);
        }

        // Fetch meteorites from NASA API
        async function fetchMeteorites() {
            const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=50000';

            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const data = await response.json();
                updateMeteoriteData(data);
            } catch (error) {
                console.error('Error fetching meteorite data:', error);
            }
        }

        // Update meteorite data on the map
        function updateMeteoriteData(meteorites) {
            // Remove existing entities
            viewer.entities.removeAll();

            meteorites.forEach(meteorite => {
                // Ensure geolocation data exists
                if (meteorite.geolocation && meteorite.geolocation.coordinates) {
                    const [lon, lat] = meteorite.geolocation.coordinates;
                    const name = meteorite.name || 'Unknown';
                    const mass = meteorite.mass ? Number(meteorite.mass) : 0;
                    const recclass = meteorite.recclass || 'Unknown';
                    const year = meteorite.year ? new Date(meteorite.year).getFullYear() : 'Unknown';

                    viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(lon, lat),
                        point: {
                            pixelSize: Math.min(Math.max(mass / 1000, 5), 25),
                            color: getColor(mass),
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1
                        },
                        description: `
                            <b>Name:</b> ${name}<br>
                            <b>Mass:</b> ${mass} g<br>
                            <b>Class:</b> ${recclass}<br>
                            <b>Year:</b> ${year}
                        `
                    });
                }
            });

            if (viewer.entities.values.length > 0) {
                viewer.zoomTo(viewer.entities).otherwise(() => {
                    console.log('Zoom failed');
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
