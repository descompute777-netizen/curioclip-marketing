/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        curio: {
          bg: '#0A0A0A',
          panel: '#1A1A1A',
          accent: '#FFD700',
          danger: '#FF3B3B',
          warm: '#FF8C00',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
