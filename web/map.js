import { stations, lines, icons } from './metadata.js'
import { getLineTimes } from './api.js'

function initMap() {
    const map = L.map('map').setView([42.356428, -71.078908], 14.5);
    
    const corner1 = L.latLng(42.325532, -71.158761);
    const corner2 = L.latLng(42.400203, -71.010778);
    const bounds = L.latLngBounds(corner1, corner2);
    
    map.setMaxBounds(bounds);
    map.options.maxBoundsViscosity = 1.0;
    map.setMinZoom(14);
    map.setMaxZoom(19);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap, © CartoDB'
    }).addTo(map);

    return map;
}

function initMarkers(map) {
    let markers = {}
    for (const color of lines) {
        const data = Object.fromEntries(
            Object.entries(stations).filter(
                ([parent, metadata]) => metadata.route.includes(color)
            )
        );

        for (const [parent, metadata] of Object.entries(data)){
            if (parent in markers) continue; 

            const coords = metadata.coords;
            let ic = L.icon({
                iconUrl: icons[color],
                iconSize: [20,20]
            });

            let m = L.marker(L.latLng(coords[1], coords[0]), {icon: ic});
            m.addTo(map);

            markers[parent] = {'marker': m};

        }; 
    }

    return markers;
}

async function assignTimesToMarkers(markers){
    for (const color of lines) {
        const data = await getLineTimes(color);
        for (const [parent, times] of Object.entries(data)) {
            markers[parent][color] = times;
        }
    }
}

async function updatePopUps(){
    await assignTimesToMarkers(markers);

    for (const [parent, content] of Object.entries(markers)) {
        let html = "";

        for (const [key, data] of Object.entries(content)) {
            if (key === "marker") continue;

            html += `<div style="display:flex; gap:12px; flex-wrap:wrap;"><strong style="display:block; width:100%;">${key}</strong>`;

            for (const [dest, times] of Object.entries(data)) {
                html += `
                    <div>
                        ${dest}
                        <ul>
                            ${times.map((time) => `<li>${Object.values(time)[0]}</li>`).join("")}
                        </ul>
                    </div>`;
            }

            html += `</div>`;
        }

        content.marker.bindPopup(html, { minWidth: 300 });
    }

    console.log(markers);
};

const map = initMap();
const markers = initMarkers(map);

updatePopUps()