import { useEffect, useState } from 'react';
import { RotateCcw, ArrowRight, LoaderCircle } from 'lucide-react';
import { type Result, type Location, signalMeta, euro } from './types';

export function DecisionLab({ result }: { result: Result }) {
  const originalBudget = Number(result.profile.budget_miete_eur);
  const initial = Object.fromEntries(signalMeta.map(s => [s.key, Math.round(result.weights[s.key] * 100)]));
  const [budget, setBudget] = useState(originalBudget), [priorities, setPriorities] = useState(initial);
  const [scenario, setScenario] = useState<{ rankings: Location[]; weights: Record<string, number> }>(), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const changed = budget !== originalBudget || signalMeta.some(s => priorities[s.key] !== initial[s.key]);
  const total = Object.values(priorities).reduce((a, b) => a + b, 0);
  useEffect(() => {
    if (!changed) { setScenario(undefined); setBusy(false); setError(''); return; }
    setScenario(undefined); setError('');
    if (!total) { setBusy(false); setError('Set at least one priority above zero.'); return; }
    setBusy(true);
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const response = await fetch('/api/scenario', {method:'POST', headers:{'Content-Type':'application/json'}, signal:controller.signal, body:JSON.stringify({profile:{...result.profile,budget_miete_eur:budget},priorities})});
        const data = await response.json();
        if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Could not calculate this scenario.');
        if (!controller.signal.aborted) { setScenario(data); setBusy(false); }
      } catch (e) { if (!controller.signal.aborted) { setError(e instanceof Error ? e.message : 'Unable to calculate scenario.'); setBusy(false); } }
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [budget, priorities, result]);
  const active = changed ? scenario : result;
  const winner = active?.rankings[0], before = result.rankings[0];
  const switched = winner && winner.municipality.gemeinde !== before.municipality.gemeinde;
  const causes = winner && active ? signalMeta.map(s => ({label:s.label,points:winner.signals[s.key].score * active.weights[s.key] - before.signals[s.key].score * active.weights[s.key]})).sort((a,b)=>b.points-a.points) : [];
  return <section className="panel decision-lab"><div className="section-heading"><div><div className="eyebrow">EXPLORE THE DECISION</div><h3>What would change my decision?</h3></div><button className="secondary" disabled={!changed} onClick={() => {setBudget(originalBudget);setPriorities(initial);}}><RotateCcw size={14}/> Reset to original</button></div><p className="chart-intro">Adjust your budget and priorities to see how your shortlist responds. Your original analysis stays available.</p>
    <div className="lab-layout"><div className="lab-controls"><label htmlFor="scenario-budget">Monthly rent budget <strong>{euro(budget)}</strong></label><input id="scenario-budget" type="range" min={Math.max(200, Math.floor(originalBudget * .25))} max={Math.ceil(originalBudget * 2.5)} step="1" value={budget} onChange={e=>setBudget(Number(e.target.value))}/><p className="chart-note">Original budget: {euro(originalBudget)}</p><div className="eyebrow">WHAT MATTERS MOST?</div>{signalMeta.map(s=><div className="priority-control" key={s.key}><label htmlFor={`priority-${s.key}`}>{s.label}<strong>{total ? Math.round(priorities[s.key]/total*100) : 0}%</strong></label><input id={`priority-${s.key}`} type="range" min="0" max="100" value={priorities[s.key]} onChange={e=>setPriorities(p=>({...p,[s.key]:Number(e.target.value)}))}/></div>)}<p className="chart-note">Priority values are normalised to a combined 100%.</p></div>
    <div className="lab-results" aria-live="polite" aria-busy={busy}>{busy ? <p role="status"><LoaderCircle size={16} className="spin"/> Recalculating your shortlist…</p> : error ? <p role="alert">{error}</p> : winner && active && <><div className="lab-outcome"><span className="eyebrow">{changed ? 'YOUR SCENARIO' : 'YOUR STARTING POINT'}</span><h3>{changed ? switched ? 'A different location takes the lead.' : 'Your strongest match holds its place.' : 'See what could shift your shortlist.'}</h3><div className="lab-before-after"><div><small>Original recommendation</small><strong>{before.municipality.gemeinde}</strong><span>{before.total_score.toFixed(1)} / 100</span></div><ArrowRight size={20}/><div><small>{changed ? 'Scenario recommendation' : 'Current recommendation'}</small><strong>{winner.municipality.gemeinde}</strong><span>{winner.total_score.toFixed(1)} / 100</span></div></div>{changed && <p>{switched ? `${causes[0].label} provides the largest weighted advantage over the original winner (${causes[0].points.toFixed(1)} points) under your new priorities.` : `The leading location remains strongest with a ${winner.total_score.toFixed(1)} suitability score under this scenario.`} Budget: {euro(budget)}.</p>}</div><div className="lab-ranking"><div className="eyebrow">HOW THE SHORTLIST MOVES</div>{active.rankings.slice(0,5).map((r,i)=>{const old=result.rankings.findIndex(x=>x.municipality.gemeinde===r.municipality.gemeinde); const movement=old-i; return <div key={r.municipality.gemeinde}><span className="lab-rank">{i+1}</span><strong>{r.municipality.gemeinde}</strong><span className={movement>0?'rank-up':movement<0?'rank-down':'rank-same'}>{movement>0?`↑ ${movement}`:movement<0?`↓ ${Math.abs(movement)}`:'—'}<small>{movement ? ' places' : ' unchanged'}</small></span><b>{r.total_score.toFixed(1)}</b></div>;})}</div></>}</div></div><p className="chart-note">Calculated by the same Python scoring engine using the same candidate locations and reference dataset. Industry, customers and floor area stay fixed. This is a scenario preview; the original report remains unchanged.</p></section>;
}
