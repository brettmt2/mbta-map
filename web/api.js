import { stations } from './metadata.js'

export async function getLineTimes(color) {
    const res = await fetch(`/times/${color}`);
    const data = await res.json();

    return data;
}