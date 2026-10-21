import type { MixInput } from './types';

export type MainNavRoute = 'home' | 'studio' | 'standards' | 'technology' | 'batch';
export type StudioSubTab = 'overview' | 'predictor' | 'optimizer' | 'sustainability' | 'recommender' | 'explainability';

export function mixToQuery(mix: MixInput): string {
  const params = new URLSearchParams({
    plastic: mix.plastic_type,
    rep: String(mix.replacement_pct),
    size: String(mix.particle_size_mm),
    wc: String(mix.wc_ratio),
    additive: mix.additive_type,
    add: String(mix.additive_pct),
    temp: String(mix.curing_temp_c),
    days: String(mix.curing_days),
  });
  return params.toString();
}

export function mixFromQuery(search: string): MixInput | null {
  const params = new URLSearchParams(search);
  if (!params.has('plastic') && !params.has('rep')) return null;
  const num = (key: string, fallback: number) => {
    const value = Number(params.get(key));
    return Number.isFinite(value) ? value : fallback;
  };
  return {
    plastic_type: params.get('plastic') || 'PET',
    replacement_pct: num('rep', 15),
    particle_size_mm: num('size', 4),
    wc_ratio: num('wc', 0.45),
    additive_type: params.get('additive') || 'fly_ash',
    additive_pct: num('add', 10),
    curing_temp_c: num('temp', 27),
    curing_days: Math.round(num('days', 28)),
  };
}

export function pathFor(route: MainNavRoute, tab: StudioSubTab, batchId: string | null): string {
  if (route === 'batch' && batchId) return `/batch/${encodeURIComponent(batchId)}`;
  if (route === 'standards') return '/standards';
  if (route === 'technology') return '/technology';
  if (route === 'studio') return tab === 'overview' ? '/studio' : `/studio/${tab}`;
  return '/';
}

export function readLocation(): { route: MainNavRoute; tab: StudioSubTab; batchId: string | null } {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  if (path.startsWith('/batch/')) {
    return { route: 'batch', tab: 'overview', batchId: decodeURIComponent(path.slice('/batch/'.length)) };
  }
  if (path === '/standards') return { route: 'standards', tab: 'overview', batchId: null };
  if (path === '/technology') return { route: 'technology', tab: 'overview', batchId: null };
  if (path === '/studio/predictor') return { route: 'studio', tab: 'predictor', batchId: null };
  if (path === '/studio/optimizer') return { route: 'studio', tab: 'optimizer', batchId: null };
  if (path === '/studio/sustainability') return { route: 'studio', tab: 'sustainability', batchId: null };
  if (path === '/studio/recommender') return { route: 'studio', tab: 'recommender', batchId: null };
  if (path === '/studio/explainability') return { route: 'studio', tab: 'explainability', batchId: null };
  if (path === '/studio') return { route: 'studio', tab: 'overview', batchId: null };
  return { route: 'home', tab: 'overview', batchId: null };
}
