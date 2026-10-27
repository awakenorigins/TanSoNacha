/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        // Tàng Kinh Các palette — gỗ đàn hương + đồng cổ + mực + giấy ngà
        bronze: { DEFAULT: '#8B6F2E', light: '#C9A66B', dark: '#5C4A1F' },
        parchment: { DEFAULT: '#F2E8D5', warm: '#F8F1E0', deep: '#E8DBC2' },
        sandalwood: { DEFAULT: '#6B4226', light: '#A67750', dark: '#3E2614' },
        ink: { DEFAULT: '#1F1A14', light: '#3C342A' },
        jade: { DEFAULT: '#4A6B5C', light: '#7A9789' },
        'red-seal': '#8B1A1F',
        // Legacy aliases for backward compat with old class names in pages
        gold: { DEFAULT: '#8B6F2E', light: '#C9A66B', dark: '#5C4A1F' },
        cream: { DEFAULT: '#F2E8D5', warm: '#F8F1E0' },
        sage: { DEFAULT: '#4A6B5C', light: '#7A9789' },
        charcoal: { DEFAULT: '#1F1A14', light: '#3C342A' },
        'red-deep': '#8B1A1F',
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        chinese: ['Noto Serif TC', 'serif'],
        brush: ['Ma Shan Zheng', 'Noto Serif TC', 'serif'],
        accent: ['Cormorant Garamond', 'Georgia', 'serif'],
      },
      fontSize: {
        'display-xl': ['5.61rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-lg': ['4.209rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display': ['3.157rem', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },
      boxShadow: {
        'bronze': '0 4px 16px rgba(139,111,46,0.25)',
        'gold': '0 4px 16px rgba(139,111,46,0.25)',
        'card': '0 4px 12px rgba(31,26,20,0.10)',
        'elevated': '0 8px 24px rgba(31,26,20,0.15)',
        'scroll': '0 2px 12px rgba(107,66,38,0.18)',
      },
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
        '800': '800ms',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scrollUnfurl: {
          '0%': { opacity: '0', transform: 'scaleY(0.3)' },
          '100%': { opacity: '1', transform: 'scaleY(1)' },
        },
      },
      animation: {
        'fade-up': 'fadeUp 0.8s ease-out forwards',
        'fade-in': 'fadeIn 0.6s ease forwards',
        'unfurl': 'scrollUnfurl 1.2s ease-out forwards',
      },
    },
  },
  plugins: [],
};
