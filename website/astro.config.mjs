import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [tailwind()],
  output: 'static',
  site: 'https://tangkinhcac.62.146.238.213.sslip.io',
  compressHTML: true,
  build: {
    inlineStylesheets: 'auto',
  },
});
