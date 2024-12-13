
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

document.getElementById('applyFiltersButton').addEventListener('click', () => {
    disableFilterInputs();
    showLoadingIndicator();
    setTimeout(() => {
        applyFilters();
        hideLoadingIndicator();
        enableFilterInputs();
    }, 100);
});


function updateTotalCounts() {
    document.getElementById('totalMeteorites').innerText = `Total Meteorites: ${filteredMeteorites.length}`;
    document.getElementById('totalCraters').innerText = `Total Impact Craters: ${filteredCraters.length}`;
}

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
