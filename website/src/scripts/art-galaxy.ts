export function mount(host: HTMLElement) {
  const layer = document.createElement('div');
  layer.className = 'sacred-galaxy'; layer.setAttribute('aria-hidden', 'true');
  host.prepend(layer);
  return { pause: () => layer.classList.add('is-paused'), resume: () => layer.classList.remove('is-paused'), destroy: () => layer.remove() };
}
