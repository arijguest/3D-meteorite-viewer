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
                        updateCraterSlidersDisplay();
                    } else {
                        alert('Invalid input. Please enter valid numbers where min ≤ max.');
                    }
                }
            }
        });
    });
}

// Initialize sliders and filters
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
    const sliderMaxDiameter = 280;
    const minAge = Math.min(...ages);
    const maxAge = Math.max(...ages);

    const diameterRangeMin = document.getElementById('diameterRangeMin');
    const diameterRangeMax = document.getElementById('diameterRangeMax');
    const ageRangeMin = document.getElementById('ageRangeMin');
    const ageRangeMax = document.getElementById('ageRangeMax');

    diameterRangeMin.min = minDiameter;
    diameterRangeMin.max = sliderMaxDiameter;
    diameterRangeMin.value = minDiameter;

    diameterRangeMax.min = minDiameter;
    diameterRangeMax.max = sliderMaxDiameter;
    diameterRangeMax.value = sliderMaxDiameter;

    ageRangeMin.min = minAge;
    ageRangeMin.max = maxAge;
    ageRangeMin.value = minAge;

    ageRangeMax.min = minAge;
    ageRangeMax.max = maxAge;
    ageRangeMax.value = maxAge;

    updateCraterSlidersDisplay();
}

// Update slider displays
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

// Populate filter options
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

// Reset filters
function resetFilters() {
    disableFilterInputs();
    showLoadingIndicator();

    initializeSliders();

    ['meteoriteClassSelect', 'targetRockSelect', 'craterTypeSelect'].forEach(selectId => {
        const selectElem = document.getElementById(selectId);
        for (let i = 0; i < selectElem.options.length; i++) {
            selectElem.options[i].selected = false;
        }
    });

    setTimeout(() => {
        applyFilters();
        hideLoadingIndicator();
        enableFilterInputs();
    }, 100);
}

// Initialize meteorite filters
function initializeMeteoriteFilters() {
    populateMeteoriteClassOptions();
    initializeMeteoriteSliders();
}

// Search bar function
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

// Populate target rock dropdown
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

// Initialize all options
function initializeOptions() {
    makeRangeEditable();
    initializeSliders();
    initializeCraterSliders();
    populateTargetRockOptions();
    populateMeteoriteClassOptions();
    populateCraterTypeOptions();

    // Event listeners for range inputs
    document.getElementById('yearRangeMin').addEventListener('input', updateSlidersDisplay);
    document.getElementById('yearRangeMax').addEventListener('input', updateSlidersDisplay);
    document.getElementById('massRangeMin').addEventListener('input', updateSlidersDisplay);
    document.getElementById('massRangeMax').addEventListener('input', updateSlidersDisplay);
    document.getElementById('diameterRangeMin').addEventListener('input', updateCraterSlidersDisplay);
    document.getElementById('diameterRangeMax').addEventListener('input', updateCraterSlidersDisplay);
    document.getElementById('ageRangeMin').addEventListener('input', updateCraterSlidersDisplay);
    document.getElementById('ageRangeMax').addEventListener('input', updateCraterSlidersDisplay);

    // Event listeners for search bar
    document.getElementById('searchButton').onclick = searchLocation;
    document.getElementById('searchInput').onkeydown = e => { if (e.key === 'Enter') searchLocation(); };

    // Event listeners for toggles and clustering
    document.getElementById('toggleMeteorites').addEventListener('change', function() {
        meteoriteDataSource.show = this.checked;
    });

    document.getElementById('clusterMeteorites').addEventListener('change', function() {
        meteoriteDataSource.clustering.enabled = this.checked;
    });

    document.getElementById('toggleCraters').addEventListener('change', function() {
        craterEntities.show = this.checked;
    });

    // Event listeners for buttons
    document.getElementById('applyFiltersButton').addEventListener('click', () => {
        disableFilterInputs();
        showLoadingIndicator();
        setTimeout(() => {
            applyFilters();
            hideLoadingIndicator();
            enableFilterInputs();
        }, 100);
    });

    document.getElementById('refreshButton').addEventListener('click', resetFilters);
}

// Export necessary functions
window.makeRangeEditable = makeRangeEditable;
window.initializeOptions = initializeOptions;
window.updateSlidersDisplay = updateSlidersDisplay;
window.updateCraterSlidersDisplay = updateCraterSlidersDisplay;
window.resetFilters = resetFilters;
