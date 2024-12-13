// Initialize Cesium viewer
Cesium.Ion.defaultAccessToken = cesiumToken;
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

// Initialize color scheme options
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
            { threshold: 50,  color: Cesium.Color.YELLOW.withAlpha(0.8) },
            { threshold: 10,   color: Cesium.Color.LIGHTYELLOW.withAlpha(0.8) },
            { threshold: 5,  color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
        ]
    },
    'Blue Scale': {
        name: 'Default2',
        description: 'Dark Blue to Light Blue',
        colors: [
            { threshold: 500000, color: Cesium.Color.DARKBLUE.withAlpha(0.6) },
            { threshold: 100000, color: Cesium.Color.BLUE.withAlpha(0.6) },
            { threshold: 50000,  color: Cesium.Color.SKYBLUE.withAlpha(0.6) },
            { threshold: 10000,  color: Cesium.Color.CYAN.withAlpha(0.6) },
            { threshold: 5000,      color: Cesium.Color.LIGHTCYAN.withAlpha(0.6) }
        ],
        craterColors: [
            { threshold: 200, color: Cesium.Color.DARKBLUE.withAlpha(0.8) },
            { threshold: 100, color: Cesium.Color.BLUE.withAlpha(0.8) },
            { threshold: 50, color: Cesium.Color.SKYBLUE.withAlpha(0.8) },
            { threshold: 10,  color: Cesium.Color.LIGHTBLUE.withAlpha(0.8) },
            { threshold: 5,  color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
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
            { threshold: 5000,      color: Cesium.Color.YELLOWGREEN.withAlpha(0.6) }
        ],
        craterColors: [
            { threshold: 200, color: Cesium.Color.DARKGREEN.withAlpha(0.8) },
            { threshold: 100, color: Cesium.Color.GREEN.withAlpha(0.8) },
            { threshold: 50, color: Cesium.Color.LIME.withAlpha(0.8) },
            { threshold: 10,  color: Cesium.Color.LIGHTGREEN.withAlpha(0.8) },
            { threshold: 5,  color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
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
            { threshold: 5000,      color: Cesium.Color.LAVENDER.withAlpha(0.6) }
        ],
        craterColors: [
            { threshold: 200, color: Cesium.Color.DARKVIOLET.withAlpha(0.8) },
            { threshold: 100, color: Cesium.Color.BLUEVIOLET.withAlpha(0.8) },
            { threshold: 50, color: Cesium.Color.VIOLET.withAlpha(0.8) },
            { threshold: 10,  color: Cesium.Color.PLUM.withAlpha(0.8) },
            { threshold: 5,  color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
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
            { threshold: 5000,      color: Cesium.Color.WHEAT.withAlpha(0.6) }
        ],
        craterColors: [
            { threshold: 200, color: Cesium.Color.SIENNA.withAlpha(0.8) },
            { threshold: 100, color: Cesium.Color.SADDLEBROWN.withAlpha(0.8) },
            { threshold: 50, color: Cesium.Color.PERU.withAlpha(0.8) },
            { threshold: 10,  color: Cesium.Color.BURLYWOOD.withAlpha(0.8) },
            { threshold: 5,  color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
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
            { threshold: 5000,      color: Cesium.Color.fromCssColorString('#F0E442').withAlpha(0.6) }
        ],
        craterColors: [
            { threshold: 200, color: Cesium.Color.fromCssColorString('#CC79A7').withAlpha(0.8) },
            { threshold: 100, color: Cesium.Color.fromCssColorString('#0072B2').withAlpha(0.8) },
            { threshold: 50, color: Cesium.Color.fromCssColorString('#009E73').withAlpha(0.8) },
            { threshold: 10,  color: Cesium.Color.fromCssColorString('#D55E00').withAlpha(0.8) },
            { threshold: 5,  color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
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
            { threshold: 5000,      color: Cesium.Color.fromCssColorString('#DDCC77').withAlpha(0.6) }
        ],
        craterColors: [
            { threshold: 200, color: Cesium.Color.fromCssColorString('#117733').withAlpha(0.8) },
            { threshold: 100, color: Cesium.Color.fromCssColorString('#332288').withAlpha(0.8) },
            { threshold: 50, color: Cesium.Color.fromCssColorString('#44AA99').withAlpha(0.8) },
            { threshold: 10,  color: Cesium.Color.fromCssColorString('#88CCEE').withAlpha(0.8) },
            { threshold: 5,  color: Cesium.Color.MINTCREAM.withAlpha(0.8) }
        ]
    }
};

// Make colorSchemes globally available
window.colorSchemes = colorSchemes;

// Initialize data sources
let meteoriteDataSource = new Cesium.CustomDataSource('meteorites');
viewer.dataSources.add(meteoriteDataSource);

let craterEntities = new Cesium.CustomDataSource('craters');
viewer.dataSources.add(craterEntities);

// Initialize arrays
let allMeteorites = [];
let filteredMeteorites = [];
let meteoriteEntities = [];
let craterEntitiesList = [];
let filteredCraters = [];
const allCraters = impactCraters.features;

// Initialize crater property names
let craterPropertyNames = [];
if (allCraters.length > 0) {
    craterPropertyNames = Object.keys(allCraters[0].properties);
    const desiredOrder = ['Name', 'Continent', 'Country', 'Age [Myr]', 'Crater diamter [km]', 'Crater type'];
    craterPropertyNames = desiredOrder.concat(craterPropertyNames.filter(item => !desiredOrder.includes(item)));
}

// Loading indicator functions
function showLoadingIndicator() {
    document.getElementById('loadingIndicator').style.display = 'block';
}

function hideLoadingIndicator() {
    document.getElementById('loadingIndicator').style.display = 'none';
}

window.hideLoadingIndicator = hideLoadingIndicator;

// Filter input control functions
function disableFilterInputs() {
    document.querySelectorAll('#controls input, #controls select, #controls button').forEach(elem => {
        elem.disabled = true;
    });
}

function enableFilterInputs() {
    document.querySelectorAll('#controls input, #controls select, #controls button').forEach(elem => {
        elem.disabled = false;
    });
}

// Initialize event handler for camera changes
viewer.camera.changed.addEventListener(updateClusteringOnZoom);

function updateClusteringOnZoom() {
    const altitude = viewer.camera.positionCartographic.height;
    if (altitude < 500000) {
        meteoriteDataSource.clustering.enabled = false;
    } else {
        meteoriteDataSource.clustering.enabled = document.getElementById('clusterMeteorites').checked;
    }
}

// Initialize age data parsing
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

// Export necessary variables and functions
window.viewer = viewer;
window.meteoriteDataSource = meteoriteDataSource;
window.craterEntities = craterEntities;
window.allMeteorites = allMeteorites;
window.filteredMeteorites = filteredMeteorites;
window.meteoriteEntities = meteoriteEntities;
window.craterEntitiesList = craterEntitiesList;
window.filteredCraters = filteredCraters;
window.allCraters = allCraters;
window.craterPropertyNames = craterPropertyNames;
window.showLoadingIndicator = showLoadingIndicator;
window.hideLoadingIndicator = hideLoadingIndicator;
window.disableFilterInputs = disableFilterInputs;
window.enableFilterInputs = enableFilterInputs;

// Function to fetch all meteorites
function fetchAllMeteorites() {
    showLoadingIndicator();
    const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=50000';

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok, status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            window.allMeteorites = data;
            initializeOptions();
            applyFilters();              
            hideLoadingIndicator();
        })
        .catch(error => {
            console.error('Error fetching meteorite data:', error);
            hideLoadingIndicator();
            alert('Failed to load meteorite data. Please try again later.');
        });
}

// Start loading app when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    fetchAllMeteorites();
});