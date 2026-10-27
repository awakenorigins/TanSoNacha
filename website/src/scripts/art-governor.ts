type ArtTier = 0 | 1 | 2;
type ArtEnv = { reduced: boolean; saveData: boolean; memory?: number; cores?: number; hidden?: boolean; webgl?: boolean; cap?: ArtTier | null };

function storedCap(): ArtTier | null {
  try {
    const raw = localStorage.getItem('artTier');
    if (raw === null || raw === '') return null;
    const value = Number(raw);
    return Number.isInteger(value) && value >= 0 && value <= 2 ? value as ArtTier : null;
  } catch { return null; }
}

/** Capability tier. User override is deliberately a cap: it can never force expensive art. */
export function chooseArtTier(env: ArtEnv): ArtTier {
  if (env.reduced || env.saveData) return 0;
  const memory = env.memory ?? 4;
  const cores = env.cores ?? 4;
  let tier: ArtTier = memory < 2 || cores < 2 ? 0 : memory < 4 || cores < 4 ? 1 : 2;
  if (tier === 2 && env.webgl === false) tier = 1;
  if (env.cap !== null && env.cap !== undefined) tier = Math.min(tier, env.cap) as ArtTier;
  return tier;
}

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'));
  } catch { return false; }
}

async function boot() {
  const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
  const nav = navigator as Navigator & { deviceMemory?: number };
  const media = matchMedia('(prefers-reduced-motion: reduce)');
  const root = document.documentElement;
  const cap = storedCap();
  const webgl = supportsWebGL();
  let controller: { pause(): void; resume(): void; destroy(): void } | undefined;
  let generation = 0;

  const tierNow = () => chooseArtTier({ reduced: media.matches, saveData: !!connection?.saveData, memory: nav.deviceMemory, cores: navigator.hardwareConcurrency, hidden: document.hidden, webgl, cap });
  const start = async () => {
    const current = ++generation;
    controller?.destroy(); controller = undefined;
    const tier = tierNow();
    root.dataset.artTier = String(tier);
    root.classList.toggle('art-paused', document.hidden);
    const host = document.querySelector<HTMLElement>('[data-adaptive-art]');
    if (!host || tier === 0) return;
    try {
      const module = tier === 2 ? await import('./art-hyperspeed') : await import('./art-galaxy');
      if (current !== generation || tierNow() !== tier) return;
      controller = module.mount(host);
      if (document.hidden) controller.pause();
    } catch {
      root.dataset.artTier = '0';
      controller?.destroy(); controller = undefined;
    }
  };
  const visibility = () => {
    root.classList.toggle('art-paused', document.hidden);
    document.hidden ? controller?.pause() : controller?.resume();
  };
  document.addEventListener('visibilitychange', visibility);
  media.addEventListener?.('change', start);
  await start();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
else void boot();
