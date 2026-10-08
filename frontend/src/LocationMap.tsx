import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import boundaryData from './district-boundaries.json';
type GeoJsonObject = NonNullable<Parameters<typeof L.geoJSON>[0]>;
import { ArrowUpRight, Focus, MapPin, Maximize2 } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import geographyData from './geography.json';
import type { Location } from './types';

type Geography = { lat: number; lon: number; precision: string; zoom: number; source: string; verified_on: string };
const displayName = (name: string) => name.replace(/Wien \((1|7|10)\., /, (_, n) => `Wien (${n}${n === '1' ? 'st' : 'th'} district, `);
const geography: Record<string, Geography> = Object.fromEntries(Object.entries(geographyData).map(([name, value]) => [displayName(name), value]));
const districtBoundaries = Object.fromEntries(Object.entries(boundaryData).map(([name, value]) => [displayName(name), value])) as unknown as Record<string, GeoJsonObject>;

export function LocationMap({ rankings, selected, onSelect }: { rankings: Location[]; selected: number; onSelect: (index: number) => void }) {
  const container = useRef<HTMLDivElement>(null), map = useRef<L.Map | null>(null);
  const markers = useRef<L.Marker[]>([]), boundary = useRef<L.FeatureGroup | null>(null);
  const [picks, setPicks] = useState<number[]>([selected]);
  const [all, setAll] = useState(false), [tilesFailed, setTilesFailed] = useState(false);
  const toggleLocation = (index: number) => {
    setAll(false);
    const next = all ? [index] : picks.includes(index) ? picks.filter(i => i !== index) : [...picks, index];
    if (!next.length) return;
    setPicks(next);
    onSelect(next.includes(index) ? index : next[next.length - 1]);
  };
  const toggleRef = useRef(toggleLocation);
  toggleRef.current = toggleLocation;
  const location = rankings[selected], geo = geography[location.municipality.gemeinde];

  useEffect(() => {
    if (!container.current) return;
    const m = L.map(container.current, { scrollWheelZoom: false, zoomControl: false }).setView([geo.lat, geo.lon], geo.zoom);
    map.current = m;
    L.control.zoom({ position: 'topright' }).addTo(m);
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · District boundaries: <a href="https://data.wien.gv.at">Stadt Wien</a>' }).addTo(m);
    tiles.on('tileerror', () => setTilesFailed(true));
    L.control.scale({ position: 'bottomleft', imperial: false }).addTo(m);
    const resize = new ResizeObserver(() => m.invalidateSize({ animate: false }));
    resize.observe(container.current);
    return () => { resize.disconnect(); m.remove(); map.current = null; };
  }, []);

  useEffect(() => {
    const m = map.current;
    if (!m) return;
    markers.current.forEach(marker => marker.remove());
    markers.current = rankings.map((r, i) => {
      const g = geography[r.municipality.gemeinde];
      if (!g) return null;
      const icon = L.divIcon({ className: 'location-marker-wrapper', html: `<span class="location-marker ${(all || picks.includes(i)) ? 'is-selected' : ''}"><span>${i + 1}</span></span>`, iconSize: [32, 38], iconAnchor: [16, 34], tooltipAnchor: [0, -36] });
      const marker = L.marker([g.lat, g.lon], { icon, title: `${i + 1}. ${r.municipality.gemeinde}`, alt: r.municipality.gemeinde, zIndexOffset: (all || picks.includes(i)) ? 1000 : 0 }).addTo(m);
      const tooltip = document.createElement('div');
      const name = document.createElement('strong'); name.textContent = r.municipality.gemeinde;
      const score = document.createElement('span'); score.textContent = `${r.total_score.toFixed(1)} / 100 · ${g.precision === 'district' ? 'District reference point' : 'City-centre reference point'}`;
      tooltip.append(name, document.createElement('br'), score);
      marker.bindTooltip(tooltip, { direction: 'top', opacity: 1 });
      marker.on('click', () => toggleRef.current(i));
      return marker;
    }).filter((m): m is L.Marker => m !== null);
    boundary.current?.remove();
    boundary.current = null;
    const visible = all ? rankings.map((_, i) => i) : picks;
    const shapes = visible.flatMap(i => { const shape = districtBoundaries[rankings[i].municipality.gemeinde]; return shape ? [L.geoJSON(shape, { style: { color: '#3558a7', weight: 2, fillColor: '#6386c5', fillOpacity: .12 }, interactive: false })] : []; });
    if (shapes.length) boundary.current = L.featureGroup(shapes).addTo(m);
    const bounds = L.latLngBounds(visible.flatMap(i => { const g = geography[rankings[i].municipality.gemeinde]; return g ? [[g.lat, g.lon] as L.LatLngTuple] : []; }));
    if (boundary.current) bounds.extend(boundary.current.getBounds());
    const single = geography[rankings[visible[0]].municipality.gemeinde];
    const animate = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    m.stop();
    if (visible.length === 1 && !boundary.current) m.setView([single.lat, single.lon], single.zoom, { animate });
    else if (bounds.isValid()) m.fitBounds(bounds, { padding: [45, 45], maxZoom: visible.length === 1 ? 15 : 13, animate });
  }, [rankings, picks, all]);

  return <section className="panel map-panel"><div className="map-heading"><div><div className="eyebrow">PUT YOUR SHORTLIST ON THE MAP</div><h3>{all ? 'Your locations across Austria' : picks.length > 1 ? `Compare ${picks.length} locations` : rankings[picks[0]].municipality.gemeinde}</h3><p>Select cities or districts below. The map automatically adjusts to keep your selection in view.</p></div><div className="map-actions"><button className={!all ? 'active' : ''} onClick={() => {setAll(false);setPicks([selected]);}}><Focus size={14}/> Focus one</button><button className={all ? 'active' : ''} onClick={() => setAll(true)}><Maximize2 size={14}/> All locations</button></div></div>
    <div className="map-layout"><div><div ref={container} className="location-map" aria-label={`Interactive map: ${all ? 'all shortlisted locations' : picks.map(i => rankings[i].municipality.gemeinde).join(', ')}`}/>{tilesFailed && <p className="map-warning" role="status">Some map tiles could not load. Markers and coordinates remain available; <a href={`https://www.openstreetmap.org/?mlat=${geo.lat}&mlon=${geo.lon}#map=${geo.zoom}/${geo.lat}/${geo.lon}`} target="_blank" rel="noreferrer">open the selected location in OpenStreetMap</a>.</p>}<div className="map-detail"><span className="map-detail-icon"><MapPin size={18}/></span><div><strong>{location.municipality.gemeinde}</strong><p>{location.municipality.bundesland} · {geo.lat.toFixed(5)}° N, {geo.lon.toFixed(5)}° E</p><small>{geo.precision === 'district' ? 'District reference point' : 'Representative city-centre point'}{districtBoundaries[location.municipality.gemeinde] ? ' · Official district boundary shown' : ''}</small></div><a aria-label={`Open ${location.municipality.gemeinde} in OpenStreetMap`} href={`https://www.openstreetmap.org/?mlat=${geo.lat}&mlon=${geo.lon}#map=${geo.zoom}/${geo.lat}/${geo.lon}`} target="_blank" rel="noreferrer"><ArrowUpRight size={19}/></a></div></div>
    <div className="map-shortlist"><div className="eyebrow">COMPARE LOCATIONS</div>{rankings.map((r, i) => <button key={r.municipality.gemeinde} aria-pressed={all || picks.includes(i)} className={(all || picks.includes(i)) ? 'active' : ''} onClick={() => toggleLocation(i)}><span className="map-rank">{i + 1}</span><span><strong>{r.municipality.gemeinde}</strong><small>{r.municipality.bundesland}</small></span><b>{r.total_score.toFixed(1)}</b></button>)}</div></div>
    <p className="map-note">Pins locate the named area, not a specific property. Centre labels in the synthetic dataset are representative points, not surveyed boundaries. <a href={geo.source} target="_blank" rel="noreferrer">Coordinate source</a> · Checked {geo.verified_on}.</p>
  </section>;
}
