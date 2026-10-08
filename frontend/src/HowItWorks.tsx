import type { MouseEvent } from 'react';
import { ArrowLeft, Users, Building2, Wallet, TrainFront } from 'lucide-react';
import { CitySkyline } from './CitySkyline';
import { signalMeta } from './types';

export function HowItWorks({ onBack }: { onBack: (event: MouseEvent<HTMLAnchorElement>) => void }) {
  const icons = [Users, Building2, Wallet, TrainFront];
  const descriptions = [
    'Find areas whose residents match the customers you want to reach.',
    'Explore the nearby shops, services and amenities that shape a neighbourhood.',
    'See how estimated rental costs fit the space you need and the budget you have.',
    'Understand how easily customers can reach your location by public transport.',
  ];
  return <main className="how-page">
    <a className="back-analysis" href="/" onClick={onBack}><ArrowLeft size={16}/> Back to analysis</a>
    <section className="how-hero"><div className="how-hero-copy"><div className="eyebrow">YOUR NEXT LOCATION STARTS HERE</div><h1>A clearer path.<br/><span>A more confident choice.</span></h1><p>Finding the right place for your business starts with understanding your options. With Standora, you can turn your needs into a shortlist and explore what makes each location a good fit.</p></div><CitySkyline/></section>
    <section className="how-steps" aria-label="How to find your location">{[
      ['01', 'Tell us about your business', 'Choose your business type, the customers you want to reach, your space and your budget. Let us know where you would like to look.'],
      ['02', 'Discover your shortlist', 'Our program brings your preferences together to highlight locations worth exploring, with clear summaries of their strengths and trade-offs.'],
      ['03', 'Find your best fit', 'Compare locations side by side, explore them on the map, and try different budgets and priorities in the Decision lab. Save your summary when you are ready.'],
    ].map(([number, title, text]) => <article className="panel" key={number}><span className="step-number">{number}</span><h3>{title}</h3><p>{text}</p></article>)}</section>
    <section className="how-signals"><div className="eyebrow">A VIEW OF WHAT MATTERS</div><h2>See the opportunity from every angle.</h2><div className="how-signal-grid">{signalMeta.map((signal, i) => { const Icon = icons[i]; return <article className="panel" key={signal.key}><Icon size={23}/><h3>{signal.label}</h3><p>{descriptions[i]}</p></article>; })}</div></section>
    <section className="how-notes"><article><div className="eyebrow">EXPLORE WITH CONFIDENCE</div><h2>Understand the trade-offs.</h2><p>A lively neighbourhood might cost more. A more affordable area may offer different transport options. We help you see those differences so you can choose what matters most to your business.</p></article><article><div className="eyebrow">PLAN YOUR NEXT STEP</div><h2>From shortlist to a closer look.</h2><p>Use your results to decide which areas to investigate and which questions to ask before choosing a property.</p><p className="chart-note">This demo uses illustrative data. Rental estimates are a guide, rather than available property listings.</p></article></section>
    <div className="how-return"><h2>Where could your business thrive?</h2><a className="secondary" href="/" onClick={onBack}><ArrowLeft size={16}/> Explore my locations</a><p>Your profile and results stay available while you explore this page.</p></div>
    <footer><span className="brand">standora</span><p>Find where your business belongs</p></footer>
  </main>;
}
