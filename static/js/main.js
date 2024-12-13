
if (allCraters.length > 0) {
    craterPropertyNames = Object.keys(allCraters[0].properties);

    // Reorder craterPropertyNames to ensure desired column order
    const desiredOrder = ['Name', 'Continent', 'Country', 'Age [Myr]', 'Crater diamter [km]', 'Crater type'];
    craterPropertyNames = desiredOrder.concat(craterPropertyNames.filter(item => !desiredOrder.includes(item)));
}

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
    showLoadingIndicator();
    const url = 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=50000';
    fetch(url)
        .then(response => response.json())
        .then(data => {
            allMeteorites = data;
            populateMeteoriteClassOptions();
            initializeMeteoriteSliders();
            applyFilters();
            hideLoadingIndicator();
        })
        .catch(error => {
            console.error('Error fetching meteorite data:', error);
            hideLoadingIndicator();
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
        if (id && id.properties) {
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

// Add event listener for crater type select
document.getElementById('craterTypeSelect').addEventListener('change', () => {
    applyFilters();
});


// Adjust getCraterSize function to use dynamic thresholds based on data
function getCraterSize(diameter) {
    if (diameter >= 200) return 30;
    if (diameter >= 150) return 25;
    if (diameter >= 100) return 20;
    if (diameter >= 50) return 15;
    return 10;
}

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


updateMeteoriteLegend();
updateCraterLegend();
