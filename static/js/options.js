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

// Populate filter target rock dropdown
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

// Function to update crater data based on filters
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

// Function to update meteorite data based on filters
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

// Function to update total counts in options menu
function updateTotalCounts() {
    document.getElementById('totalMeteorites').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
    document.getElementById('totalCraters').innerText = `Total Impact Craters: ${filteredCraters.length}`;
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

// Function to update top meteorites bar based on filters
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

// Function to update top craters bar based on filters
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

// Function to update meteorite view all table based on filters
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

// Function to update craters view all table based on filters
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

// Function to apply filters
function applyFilters() {
    let yearMin = parseInt(document.getElementById('yearRangeMin').value);
    let yearMax = parseInt(document.getElementById('yearRangeMax').value);
    let massMin = parseInt(document.getElementById('massRangeMin').value);
    let massMax = parseInt(document.getElementById('massRangeMax').value);

    let diameterMin = parseFloat(document.getElementById('diameterRangeMin').value);
    let diameterMax = parseFloat(document.getElementById('diameterRangeMax').value);
    let ageMin = parseFloat(document.getElementById('ageRangeMin').value);
    let ageMax = parseFloat(document.getElementById('ageRangeMax').value);
    const selectedClasses = Array.from(document.getElementById('meteoriteClassSelect').selectedOptions).map(option => option.value);
    const selectedRocks = Array.from(document.getElementById('targetRockSelect').selectedOptions).map(option => option.value);
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

    // Apply filters event handler
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
