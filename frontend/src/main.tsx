import React, { lazy, Suspense, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowUpRight, ArrowRight, MapPin, Building2, Users, TrainFront, Wallet, Download, Compass, Check, LoaderCircle, ChevronRight, SlidersHorizontal } from 'lucide-react';
import './style.css';
import { Account } from './Account';
import { type Profile, type Location, type Result } from './types';
import { DecisionLab } from './DecisionLab';
import { HowItWorks } from './HowItWorks';
import { ContributionChart, SignalChart, RentChart } from './Charts';
const LocationMap = lazy(() => import('./LocationMap').then(module => ({default: module.LocationMap}))); 
const signals = [{ key: 'demographics', label: 'Customer fit', icon: Users }, { key: 'poi', label: 'Surrounding activity', icon: Building2 }, { key: 'rent', label: 'Rent affordability', icon: Wallet }, { key: 'transit', label: 'Public transport', icon: TrainFront }];
const industries = [['retail', 'Retail and shops'], ['cafe', 'Café and gastronomy'], ['fitness', 'Fitness and wellness'], ['logistics', 'Logistics']];
const audiences = [['young_professionals', 'Young professionals (ages 25–40)'], ['students_families', 'Students and families'], ['adults_30_plus', 'Health-conscious adults (ages 30 and above)']];
const initial: Profile = { branche: 'retail', flaeche_m2: '200', zielgruppe: 'young_professionals', budget_miete_eur: '4000', region_praeferenz: ['Österreich'] };
const presets = [{ name: 'Retail expansion', profile: initial }, { name: 'Neighbourhood café', profile: { ...initial, branche: 'cafe', flaeche_m2: '100', budget_miete_eur: '2000', zielgruppe: 'students_families' } }, { name: 'Fitness studio', profile: { ...initial, branche: 'fitness', flaeche_m2: '500', budget_miete_eur: '6000', zielgruppe: 'adults_30_plus' } }];
const euro = (n: number) => new Intl.NumberFormat('en-AT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
function App() {
    const [page, setPage] = useState(window.location.pathname);
    useEffect(() => { const handleBack = () => setPage(window.location.pathname); window.addEventListener('popstate', handleBack); return () => window.removeEventListener('popstate', handleBack); }, []);
    const navigate = (e: React.MouseEvent<HTMLAnchorElement>, path: string) => { if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; e.preventDefault(); window.history.pushState({}, '', path); setPage(path); window.scrollTo(0, 0); };
    const [profile, setProfile] = useState<Profile>(initial), [config, setConfig] = useState<{
        regions: string[];
        locations: number;
        states: number;
    }>(), [result, setResult] = useState<Result>(), [selected, setSelected] = useState(0), [tab, setTab] = useState('Overview'), [busy, setBusy] = useState(false), [stage, setStage] = useState(''), [error, setError] = useState(''), [compare, setCompare] = useState<string[]>([]), [configError, setConfigError] = useState(false);
    const loadConfig = () => { setConfigError(false); fetch('/api/config').then(r => { if (!r.ok)
        throw Error(); return r.json(); }).then(setConfig).catch(() => setConfigError(true)); };
    useEffect(loadConfig, []);
    const edit = (key: keyof Profile, value: string | string[]) => setProfile(p => ({ ...p, [key]: value }));
    async function analyze(e: React.FormEvent) {
        e.preventDefault();
        setBusy(true);
        setError('');
        setResult(undefined);
        setStage('Connecting to the analysis engine');
        setSelected(0);
        setTab('Overview');
        try {
            const response = await fetch('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(profile) });
            if (!response.ok) {
                const body = await response.json();
                throw Error(typeof body.detail === 'string' ? body.detail : Array.isArray(body.detail) ? body.detail.map((x: {
                    loc: string[];
                    msg: string;
                }) => `${x.loc.at(-1)}: ${x.msg}`).join('; ') : 'Unable to start analysis');
            }
            const reader = response.body!.getReader(), decoder = new TextDecoder();
            let buffer = '', received = false;
            const process = (line: string) => { if (!line.trim())
                return; const event = JSON.parse(line); if (event.type === 'progress')
                setStage(event.stage); if (event.type === 'error')
                throw Error(event.message); if (event.type === 'result') {
                setResult(event.data);
                setCompare(event.data.rankings.slice(0, 3).map((r: Location) => r.municipality.gemeinde));
                received = true;
            } };
            while (true) {
                const { value, done } = await reader.read();
                buffer += decoder.decode(value, { stream: !done });
                const lines = buffer.split('\n');
                buffer = lines.pop()!;
                lines.forEach(process);
                if (done) {
                    process(buffer);
                    break;
                }
            }
            if (!received)
                throw Error('The connection ended before the analysis finished. Please retry.');
        }
        catch (e) {
            setError(e instanceof Error ? e.message : 'Connection failed. Please retry.');
        }
        finally {
            setBusy(false);
        }
    }
    function download() { if (!result)
        return; const url = URL.createObjectURL(new Blob([result.report_html], { type: 'text/html' })); const a = document.createElement('a'); a.href = url; a.download = 'standora-location-report.html'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
    function revealLocation(index: number) {
        setSelected(index);
        setTab('Overview');
        requestAnimationFrame(() => document.querySelector('.results-heading')?.scrollIntoView({
            block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
        }));
    }
    const current = result?.rankings[selected];
    const sorted = current ? signals.slice().sort((a, b) => current.signals[b.key].score - current.signals[a.key].score) : [];
    const toggle = (name: string) => setCompare(prev => prev.includes(name) ? prev.filter(n => n !== name) : prev.length < 3 ? [...prev, name] : prev);
    return <><header><a className="brand" href="/" onClick={e => navigate(e, '/')} aria-label="Standora home"><img className="standora-mark" src="/standora-mark.svg" alt="" width="44" height="44"/><span className="brand-lockup"><span className="brand-name">standora</span><span className="brand-tagline">Find where your business belongs</span></span></a><a className="header-link" href="/how-it-works" onClick={e => navigate(e, '/how-it-works')}>How it works <ArrowUpRight size={15}/></a><Account/><span className="badge"><span className="dot"/> Austria · Demo</span></header>
 {page === '/how-it-works' && <HowItWorks onBack={e => navigate(e, '/')}/>}<main hidden={page === '/how-it-works'}><section className="intro"><div className="intro-copy"><div className="eyebrow">A BETTER PLACE TO BUILD YOUR BUSINESS</div><h1>Your next location.<br /><span>Backed by evidence.</span></h1><p>Turn your business profile into a clear, explainable shortlist.<br className="desktop"/> Explore the opportunity. Understand the trade-offs.</p></div><div className="coverage"><div><strong>{config?.locations ?? '—'}</strong><span>candidate locations</span></div><div><strong>{config?.states ?? '—'}</strong><span>federal states</span></div><small>One transparent decision framework</small><div className="subscription-teaser"><span className="eyebrow">GO FURTHER</span><h3>Unlock deeper location insights.</h3><p>Expand your coverage and explore advanced analytics with a subscription.</p><span className="subscription-status">Coming soon</span></div></div></section>
 <div className="workspace"><aside id="business-profile" className="panel profile"><div className="panel-title"><span className="icon-box"><SlidersHorizontal size={18}/></span><div><h2>Your business profile</h2><p>Tell us what a good fit looks like.</p></div></div><form onSubmit={analyze}><label>Business type<select value={profile.branche} onChange={e => edit('branche', e.target.value)}>{industries.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label><label>Target customers<select value={profile.zielgruppe} onChange={e => edit('zielgruppe', e.target.value)}>{audiences.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label><div className="form-row"><label>Required space<div className="input-wrap"><input required type="number" min="10.01" max="100000" step="any" value={profile.flaeche_m2} onChange={e => edit('flaeche_m2', e.target.value)}/><span>m²</span></div></label><label>Monthly budget<div className="input-wrap"><input required type="number" min="200" max="10000000" step="any" value={profile.budget_miete_eur} onChange={e => edit('budget_miete_eur', e.target.value)}/><span>€</span></div></label></div><label>Preferred regions<select aria-describedby="region-help" value="" disabled={!config} onChange={e => { const v = e.target.value; if (v)
        edit('region_praeferenz', v === 'Österreich' ? ['Österreich'] : [...new Set([...profile.region_praeferenz.filter(x => x !== 'Österreich'), v])]); }}><option value="">Add a city or federal state…</option>{config?.regions.map(r => <option key={r} value={r}>{r === 'Österreich' ? 'All Austria' : r}</option>)}</select></label><div className="chips">{profile.region_praeferenz.map(r => <button type="button" key={r} aria-label={`Remove ${r}`} onClick={() => edit('region_praeferenz', profile.region_praeferenz.length > 1 ? profile.region_praeferenz.filter(x => x !== r) : ['Österreich'])}>{r === 'Österreich' ? 'All Austria' : r} <span>×</span></button>)}</div><p id="region-help" className="field-note">Matches any selected region. Salzburg covers the entire federal state.</p><button className="primary" disabled={busy || !config}>{busy ? <LoaderCircle className="spin" size={17}/> : <Compass size={17}/>} {busy ? 'Analyzing locations…' : 'Find my best locations'} {!busy && <ArrowRight size={17}/>}</button>{configError && <p role="alert">Could not connect. <button type="button" className="text-button" onClick={loadConfig}>Retry connection</button></p>}</form><div className="presets"><div className="eyebrow">OR START WITH AN EXAMPLE</div>{presets.map(p => <button key={p.name} disabled={busy} onClick={() => setProfile({ ...p.profile })}>{p.name}<ChevronRight size={15}/></button>)}</div></aside>
 <section className="results" aria-busy={busy}>{error && <div className="error" role="alert"><strong>Please check your request</strong><p>{error}</p></div>}{!result ? <div className="panel empty"><div className="empty-symbol"><Compass size={42} strokeWidth={1.3}/></div><div className="eyebrow">{busy ? 'ANALYSIS IN PROGRESS' : 'FROM POSSIBILITIES TO A PLAN'}</div><h2>{busy ? 'Finding your next opportunity' : 'Good decisions start with a clear view.'}</h2><p>{busy ? stage : 'Set your profile and discover which Austrian locations best match your business.'}</p>{!busy && <button type="button" className="primary empty-start" onClick={() => { const form = document.getElementById('business-profile'); form?.scrollIntoView({block:'start', behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'}); form?.querySelector<HTMLSelectElement>('select')?.focus({preventScroll:true}); }}><SlidersHorizontal size={17}/> Set up my business profile <ArrowRight size={17}/></button>}{busy ? <div className="loading" role="status"><LoaderCircle className="spin" size={18}/>{stage}</div> : <div className="empty-signals">{signals.map(s => <div key={s.key}><s.icon size={20}/><span>{s.label}</span></div>)}</div>}<div className="empty-bottom"><span>20 locations</span><span>4 scoring signals</span><span>Explainable results</span></div></div> : <><div className="results-heading"><div><div className="eyebrow">YOUR LOCATION SHORTLIST</div><h2>{result.rankings.length} possibilities. A clearer direction.</h2></div><button className="secondary" onClick={download}><Download size={16}/> Export report</button></div><div className="tabs" role="tablist" aria-label="Result views">{['Overview', 'Compare', 'Insights', 'Decision lab', 'Geography', 'All locations'].map(t => <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>{t}</button>)}</div>
 {tab === 'Overview' && current && <><div className="winner"><div><span className="winner-label">{selected === 0 ? '01 / YOUR STRONGEST MATCH' : `${String(selected + 1).padStart(2, '0')} / SELECTED LOCATION`}</span><h2>{current.municipality.gemeinde}</h2><p><MapPin size={15}/>{current.municipality.bundesland} · Municipality / district <button className="winner-map-link" onClick={() => setTab('Geography')}>View on map <ArrowUpRight size={12}/></button></p><div className="winner-chips"><span>Strongest signal: {sorted[0].label}</span><span>Review: {sorted.at(-1)!.label}</span></div></div><div className="score-ring" style={{ '--score': `${current.total_score * 3.6}deg` } as React.CSSProperties}><div><strong>{current.total_score.toFixed(1)}</strong><span>FIT / 100</span></div></div></div><div className="metrics"><div><span>Estimated monthly rent</span><strong>{euro(current.municipality.mietindex_eur_m2 * Number(result.profile.flaeche_m2))}</strong><small>Based on your space requirements</small></div><div><span>Rent budget difference</span><strong className={Number(result.profile.budget_miete_eur) < current.municipality.mietindex_eur_m2 * Number(result.profile.flaeche_m2) ? 'over-budget' : ''}>{euro(Math.abs(Number(result.profile.budget_miete_eur) - current.municipality.mietindex_eur_m2 * Number(result.profile.flaeche_m2)))}</strong><small>{Number(result.profile.budget_miete_eur) >= current.municipality.mietindex_eur_m2 * Number(result.profile.flaeche_m2) ? 'Available monthly headroom' : 'Above your monthly rent budget'}</small></div><div><span>Population</span><strong>{current.municipality.einwohner.toLocaleString('en-AT')}</strong><small>Municipality / district residents</small></div></div><div className="panel breakdown"><div className="section-heading"><h3>Why this location fits</h3><span>Four signals. Full transparency.</span></div>{signals.map(s => <div className="signal" key={s.key}><div className="signal-head"><span><s.icon size={17}/>{s.label}</span><strong>{current.signals[s.key].score.toFixed(1)}<small> / 100</small></strong></div><div className="bar"><span style={{ width: `${current.signals[s.key].score}%` }}/></div><details><summary>Explore the evidence</summary><p>{current.signals[s.key].reason}</p></details></div>)}</div><div className="alternatives">{result.rankings.slice(0, 3).map((r, i) => <button className={i === selected ? 'alternative active' : 'alternative'} key={r.municipality.gemeinde} onClick={() => setSelected(i)}><span className="eyebrow">{i === 0 ? 'TOP RECOMMENDATION' : `ALTERNATIVE ${i}`}</span><h3>{r.municipality.gemeinde}</h3><span>{r.municipality.bundesland}</span><strong>{r.total_score.toFixed(1)}<small> / 100</small></strong><ArrowUpRight size={17}/></button>)}</div><ContributionChart result={result} selected={selected} onSelect={revealLocation}/><div className="panel narrative"><div className="eyebrow">THE BUSINESS PERSPECTIVE · TOP RECOMMENDATION</div><h3>What this means for you</h3>{result.explanation.split('\n\n').map((p, i) => <p key={i}>{p}</p>)}</div></>}
 {tab === 'Compare' && <div className="panel comparison"><h3>Compare your options</h3><p>Select up to three locations to examine the same evidence side by side.</p><div className="chips">{result.rankings.map(r => <button key={r.municipality.gemeinde} className={compare.includes(r.municipality.gemeinde) ? 'chosen' : ''} onClick={() => toggle(r.municipality.gemeinde)} disabled={!compare.includes(r.municipality.gemeinde) && compare.length === 3}>{compare.includes(r.municipality.gemeinde) && <Check size={12}/>} {r.municipality.gemeinde}</button>)}</div>{compare.length > 0 && <SignalChart locations={result.rankings.filter(r => compare.includes(r.municipality.gemeinde))} onSelect={name => revealLocation(result.rankings.findIndex(r => r.municipality.gemeinde === name))}/>}<div className="compare-grid">{result.rankings.filter(r => compare.includes(r.municipality.gemeinde)).map(r => <article key={r.municipality.gemeinde}><span className="eyebrow">{r.municipality.bundesland}</span><h3>{r.municipality.gemeinde}</h3><div className="compare-score">{r.total_score.toFixed(1)}<small> / 100</small></div>{signals.map(s => <div className="compare-signal" key={s.key}><span>{s.label}<b>{r.signals[s.key].score.toFixed(1)}</b></span><div className="bar"><span style={{ width: `${r.signals[s.key].score}%` }}/></div></div>)}<p>Estimated rent <strong>{euro(r.municipality.mietindex_eur_m2 * Number(result.profile.flaeche_m2))}/mo</strong></p><details><summary>Strengths & trade-offs</summary>{signals.map(s => <p key={s.key}><strong>{s.label}:</strong> {r.signals[s.key].reason}</p>)}</details></article>)}</div>{compare.length === 0 && <p>Select a location above to start comparing.</p>}</div>}
 {tab === 'Insights' && <div className="insights-view"><div className="insights-intro"><h3>A closer look at your top locations</h3><p>Explore how the shortlist balances customer fit, activity, affordability and access.</p></div><RentChart locations={result.rankings.slice(0, 5)} result={result} onSelect={name => revealLocation(result.rankings.findIndex(r => r.municipality.gemeinde === name))}/><ContributionChart result={result} selected={selected} onSelect={revealLocation} limit={10}/></div>}
 {tab === 'Decision lab' && <DecisionLab key={JSON.stringify(result.profile)} result={result}/>}
 {tab === 'Geography' && <Suspense fallback={<div className="panel map-loading" role="status"><LoaderCircle className="spin" size={20}/> Loading location map…</div>}><LocationMap rankings={result.rankings} selected={selected} onSelect={setSelected}/></Suspense>}
 {tab === 'All locations' && <div className="panel table-wrap"><h3>The full ranking</h3><p>Scores are suitability indicators, not probabilities of business success.</p><table><thead><tr><th>Location</th><th>Overall</th>{signals.map(s => <th key={s.key}>{s.label}</th>)}</tr></thead><tbody>{result.rankings.map((r, i) => <tr key={r.municipality.gemeinde}><td><button className="text-button" onClick={() => revealLocation(i)}>{i + 1}. {r.municipality.gemeinde}</button><small>{r.municipality.bundesland}</small></td><td><strong>{r.total_score.toFixed(1)}</strong></td>{signals.map(s => <td key={s.key}>{r.signals[s.key].score.toFixed(1)}</td>)}</tr>)}</tbody></table></div>}
 </>}</section></div>
 <footer><span className="brand">standora</span><p>Interview demonstration · Synthetic data · Decision support, not official location advice</p><span>MADE FOR CLEARER DECISIONS</span></footer></main></>;
}
createRoot(document.getElementById('root')!).render(<App />);
