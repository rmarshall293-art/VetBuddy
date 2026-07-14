import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#1a2744',
          50: '#f0f3f8',
          100: '#d9e1ed',
          200: '#b3c3db',
          300: '#8da5c9',
          400: '#5f7aab',
          500: '#3d5a8a',
          600: '#2d4569',
          700: '#1a2744',
          800: '#141e35',
          900: '#0d1426',
        },
        sage: {
          DEFAULT: '#8fa68f',
          50: '#f4f7f4',
          100: '#e4ebe4',
          200: '#c9d6c9',
          300: '#a8bda8',
          400: '#8fa68f',
          500: '#6d8a6d',
          600: '#567056',
          700: '#445844',
        },
        cream: {
          DEFAULT: '#f7f5f0',
          50: '#fdfcfa',
          100: '#f7f5f0',
          200: '#ede9e0',
          300: '#e0d9cc',
        },
        gold: {
          DEFAULT: '#c9a227',
          light: '#e8d48a',
        },
      },
      fontFamily: {
        display: ['var(--font-libre-baskerville)', 'Georgia', 'serif'],
        sans: ['var(--font-source-sans)', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.8s ease-out forwards',
        'fade-in': 'fadeIn 1s ease-out forwards',
        float: 'float 6s ease-in-out infinite',
        shimmer: 'shimmer 8s ease-in-out infinite',
        'pulse-soft': 'pulseSoft 3s ease-in-out infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        shimmer: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
      },
      backgroundImage: {
        'hero-gradient':
          'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(143,166,143,0.25) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 100% 50%, rgba(26,39,68,0.08) 0%, transparent 50%), linear-gradient(180deg, #f7f5f0 0%, #ede9e0 100%)',
        'mesh-pattern':
          'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%231a2744\' fill-opacity=\'0.03\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
      },
    },
  },
  plugins: [],
};

export default config;
