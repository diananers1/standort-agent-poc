import { useId, useState } from 'react';
import { ArrowUpRight, BarChart3 } from 'lucide-react';
import { type Location, type Result, signalMeta, locationColors, euro } from './types';

type Props = { result: Result; selected: number; onSelect: (index: number) => void; limit?: number };
export function ContributionChart({ result, selected, onSelect, limit = 5 }: Props) {
  return <section className="panel chart-panel">
    <div className="section-heading"><div><div className="eyebrow">THE SCORE, EXPLAINED</div><h3>What puts a location ahead?</h3></div><BarChart3 size={22}/></div>
    <p className="chart-intro">Each segment shows the points a signal contributes after industry weighting. Select a location to explore its evidence.</p>
    <div className="chart-legend">{signalMeta.map(s => <span key={s.key}><i style={{ background: s.color }}/>{s.label} <b>{Math.round(result.weights[s.key] * 100)}%</b></span>)}</div>
    <div className="contribution-chart"><div className="chart-scale"><span>Weighted points</span><div>{[0, 25, 50, 75, 100].map(n => <span key={n}>{n}</span>)}</div><span>/ 100</span></div>
      {result.rankings.slice(0, limit).map((r, i) => <button key={r.municipality.gemeinde} className={`contribution-row ${selected === i ? 'selected' : ''}`} onClick={() => onSelect(i)} aria-label={`${r.municipality.gemeinde}, overall ${r.total_score.toFixed(1)}. View location details.`}>
        <span className="chart-location"><small>{String(i + 1).padStart(2, '0')}</small><span>{r.municipality.gemeinde}</span></span>
        <span className="stacked-bar">{signalMeta.map(s => { const points = r.signals[s.key].score * result.weights[s.key]; return <span key={s.key} style={{ width: `${points}%`, background: s.color }} title={`${s.label}: ${r.signals[s.key].score.toFixed(1)} × ${Math.round(result.weights[s.key] * 100)}% = ${points.toFixed(1)} points`}/>; })}</span>
        <strong>{r.total_score.toFixed(1)}<ArrowUpRight size={12}/></strong>
      </button>)}
    </div>
    <p className="chart-note">Scores are suitability indicators. Longer segments reflect weighted contributions, not market size or success probabilities.</p>
  </section>;
}

export function SignalChart({ locations, onSelect }: { locations: Location[]; onSelect: (name: string) => void }) {
  const id = useId();
  const [view, setView] = useState<'radar' | 'bars'>('radar');
  const point = (axis: number, score: number) => { const angle = axis * Math.PI / 2 - Math.PI / 2; return [380 + Math.cos(angle) * 125 * score / 100, 175 + Math.sin(angle) * 125 * score / 100]; };
  const polygon = (scores: number[]) => scores.map((score, i) => point(i, score).join(',')).join(' ');
  const width = 760, height = 330, left = 44, right = 14, top = 24, bottom = 49;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const groupWidth = plotWidth / 4, barWidth = Math.min(31, (groupWidth - 50) / Math.max(locations.length, 1));
  return <section className="panel chart-panel"><div className="section-heading"><div><div className="eyebrow">STRENGTHS & TRADE-OFFS</div><h3>Different places. Different strengths.</h3></div><div className="chart-switch" role="group" aria-label="Comparison chart style">{(['radar', 'bars'] as const).map(mode => <button key={mode} aria-pressed={view === mode} onClick={() => setView(mode)}>{mode === 'radar' ? 'Radar' : 'Bars'}</button>)}</div></div><p className="chart-intro">Compare raw signal scores on the same 0–100 scale. {view === 'radar' ? 'Each shape reveals a location’s balance; switch to bars for precise comparisons.' : 'Select a bar to explore the location.'}</p>
    <div className="chart-legend location-legend">{locations.map((r, i) => <span key={r.municipality.gemeinde}><i style={{ background: locationColors[i] }}/>{r.municipality.gemeinde}</span>)}</div>
    {view === 'radar' ? <div className="radar-chart"><svg viewBox="0 0 760 360" role="group" aria-labelledby={`${id}-radar-title ${id}-radar-desc`}>
      <title id={`${id}-radar-title`}>Location strengths on four equally scaled axes</title><desc id={`${id}-radar-desc`}>{locations.map(r => `${r.municipality.gemeinde}: ${signalMeta.map(s => `${s.label} ${r.signals[s.key].score.toFixed(1)} out of 100`).join(', ')}`).join('. ')}</desc>
      {[25, 50, 75, 100].map(score => <g key={score}><polygon points={polygon([score, score, score, score])} fill="none" stroke="#dce4ef"/><text x={386} y={175 - 125 * score / 100 + 14} className="axis-label">{score}</text></g>)}
      {signalMeta.map((s, i) => { const [x, y] = point(i, 100); const [lx, ly] = point(i, 128); return <g key={s.key}><line x1="380" y1="175" x2={x} y2={y} stroke="#dce4ef"/><text x={lx} y={ly + 5} textAnchor={i === 1 ? 'start' : i === 3 ? 'end' : 'middle'} className="axis-label">{s.label}</text></g>; })}
      {locations.map((r, ri) => <g key={r.municipality.gemeinde}><polygon points={polygon(signalMeta.map(s => r.signals[s.key].score))} fill={locationColors[ri]} fillOpacity=".09" stroke={locationColors[ri]} strokeWidth="2.5" strokeDasharray={[undefined, '7 4', '2 4'][ri]}/>{signalMeta.map((s, i) => { const [x, y] = point(i, r.signals[s.key].score); return <g key={s.key}><title>{r.municipality.gemeinde}: {s.label} {r.signals[s.key].score.toFixed(1)} / 100</title><circle cx={x} cy={y} r="9" fill="transparent"/><circle cx={x} cy={y} r="4" fill={locationColors[ri]} stroke="white" strokeWidth="1.5"/></g>; })}</g>)}
    </svg><p className="chart-note">Further from the centre means a stronger signal. Shape area does not represent the weighted overall score.</p></div> : <div className="svg-chart"><svg viewBox={`0 0 ${width} ${height}`} role="group" aria-labelledby={`${id}-title ${id}-desc`}>
      <title id={`${id}-title`}>Signal scores for selected locations</title><desc id={`${id}-desc`}>{locations.map(r => `${r.municipality.gemeinde}: ${signalMeta.map(s => `${s.label} ${r.signals[s.key].score.toFixed(1)}`).join(', ')}`).join('. ')}</desc>
      {[0, 25, 50, 75, 100].map(score => { const y = top + plotHeight * (1 - score / 100); return <g key={score}><line x1={left} x2={width - right} y1={y} y2={y} stroke="#e4eaf3" strokeDasharray={score ? '3 4' : undefined}/><text x={left - 11} y={y + 4} textAnchor="end" className="axis-label">{score}</text></g>; })}
      {signalMeta.map((s, si) => <g key={s.key}><text x={left + groupWidth * (si + .5)} y={height - 20} textAnchor="middle" className="axis-label">{s.label}</text>{locations.map((r, ri) => { const score = r.signals[s.key].score, barHeight = plotHeight * score / 100; const x = left + groupWidth * (si + .5) - locations.length * (barWidth + 7) / 2 + ri * (barWidth + 7); const select = () => onSelect(r.municipality.gemeinde); return <g key={r.municipality.gemeinde} role="button" tabIndex={0} aria-label={`${r.municipality.gemeinde}, ${s.label}: ${score.toFixed(1)} of 100. View details.`} onClick={select} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(); } }} className="chart-hit"><title>{r.municipality.gemeinde}: {s.label} {score.toFixed(1)} / 100</title><rect x={x} y={top + plotHeight - Math.max(barHeight, 2)} width={barWidth} height={Math.max(barHeight, 2)} rx={4} fill={locationColors[ri]}/><text x={x + barWidth / 2} y={top + plotHeight - barHeight - 8} textAnchor="middle" className="value-label">{score.toFixed(0)}</text></g>; })}</g>)}
    </svg></div>}
  </section>;
}

export function RentChart({ locations, result, onSelect }: { locations: Location[]; result: Result; onSelect: (name: string) => void }) {
  const budget = Number(result.profile.budget_miete_eur), area = Number(result.profile.flaeche_m2);
  const max = Math.max(budget, ...locations.map(r => r.municipality.mietindex_eur_m2 * area)) * 1.15;
  const budgetPosition = budget / max * 100;
  return <section className="panel chart-panel rent-chart"><div className="eyebrow">THE COST OF YOUR SHORTLIST</div><h3>Does the rent fit your budget?</h3><p className="chart-intro">Illustrative monthly rent for {area.toLocaleString('en-AT')} m². The dashed line marks your {euro(budget)} monthly budget.</p>
    <div className="rent-legend"><span><i className="budget-key"/>Monthly budget</span><span><i style={{ background: '#3558a7' }}/>Within budget</span><span><i style={{ background: '#d5983e' }}/>Above budget</span></div>
    <div className="rent-scale"><span>{euro(0)}</span><span>{euro(max / 2)}</span><span>{euro(max)}</span></div>
    {locations.map(r => { const rent = r.municipality.mietindex_eur_m2 * area, difference = budget - rent; return <button className="rent-row" key={r.municipality.gemeinde} onClick={() => onSelect(r.municipality.gemeinde)}><div><strong>{r.municipality.gemeinde}</strong><span>{euro(rent)}<small className={difference < 0 ? 'over' : ''}>{euro(Math.abs(difference))} {difference < 0 ? 'above budget' : 'headroom'}</small></span></div><span className="rent-track"><span className="rent-fill" style={{ width: `${rent / max * 100}%`, background: difference < 0 ? '#d5983e' : '#3558a7' }}/><span className="budget-line" style={{ left: `${budgetPosition}%` }}/></span></button>; })}
    <p className="chart-note">Rent index × floor area. These are synthetic estimates, not property listings. Budget influences ranking; it does not exclude a location.</p>
  </section>;
}
