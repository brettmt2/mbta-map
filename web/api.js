import { stations } from './metadata.js'

export async function getLineTimes(color) {
    const res = await fetch(`http://localhost:8000/times/${color}`);
    const data = await res.json();

    return data;
}

// let x = await getLineTimes('Orange');
// console.log(x);

// learning js... came up with this, found a better way by splitting entries
// const x = Object.fromEntries(
//     Object.entries(stations).filter(
//         (station) => Object.values(station[1])[1].includes('Red')
//     )
// );