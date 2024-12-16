/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          primary: '#0A0A1A',
          secondary: '#121228',
        },
        text: {
          primary: '#00FFD1',
          secondary: '#7E7EFF',
        },
        accent: {
          primary: '#FF00FF',
          secondary: '#00FFFF',
        },
        border: {
          color: '#3A3A5A',
        },
      },
      boxShadow: {
        'cyberpunk': '0 0 15px rgba(255, 0, 255, 0.3), 0 0 25px rgba(0, 255, 255, 0.2)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 10px rgba(255, 0, 255, 0.3)' },
          '50%': { boxShadow: '0 0 25px rgba(0, 255, 255, 0.5)' },
        }
      }
    },
  },
  plugins: [],
}
