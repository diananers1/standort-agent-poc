export type Profile = {
  branche: string;
  flaeche_m2: string;
  zielgruppe: string;
  budget_miete_eur: string;
  region_praeferenz: string[];
};
export type Location = {
  municipality: { gemeinde: string; bundesland: string; einwohner: number; mietindex_eur_m2: number };
  total_score: number;
  signals: Record<string, { score: number; reason: string }>;
};
export type Result = {
  rankings: Location[];
  weights: Record<string, number>;
  explanation: string;
  llm_status: string;
  profile: Profile;
  report_html: string;
};
export const signalMeta = [
  { key: 'demographics', label: 'Customer fit', color: '#3558a7' },
  { key: 'poi', label: 'Surrounding activity', color: '#8b86cc' },
  { key: 'rent', label: 'Rent affordability', color: '#d5983e' },
  { key: 'transit', label: 'Public transport', color: '#65a9d3' },
];
export const locationColors = ['#294f9b', '#9384c5', '#d0953c'];
export const euro = (n: number) => new Intl.NumberFormat('en-AT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
