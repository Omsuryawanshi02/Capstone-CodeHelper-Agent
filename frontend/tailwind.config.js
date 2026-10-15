/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        obsidian: {
          bg: '#111418',
          subtle: '#171B21',
          elevated: '#1D232B',
          hover: '#252D37',
          border: '#303740',
          borderSubtle: '#222832',
        },
        cockpit: {
          text: '#F4F5F7',
          muted: '#A5ADB8',
          faint: '#657080',
        },
        lime: {
          accent: '#D2F56A',
          hover: '#BFE74A',
          glow: 'rgba(210, 245, 106, 0.15)',
        },
        violet: {
          ai: '#B8A4FF',
          glow: 'rgba(184, 164, 255, 0.15)',
        },
        cyan: {
          source: '#75D9FF',
          glow: 'rgba(117, 217, 255, 0.15)',
        },
        amber: {
          warn: '#F0AE78',
          glow: 'rgba(240, 174, 120, 0.15)',
        },
        red: {
          err: '#FF6B6B',
          glow: 'rgba(255, 107, 107, 0.15)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Geist', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'SFMono-Regular', 'Menlo', 'Consolas', '"Liberation Mono"', 'monospace'],
      },
      boxShadow: {
        'panel': '0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 0 0 1px #303740',
        'glow-lime': '0 0 20px -3px rgba(210, 245, 106, 0.25)',
        'glow-violet': '0 0 20px -3px rgba(184, 164, 255, 0.25)',
      }
    },
  },
  plugins: [],
}
