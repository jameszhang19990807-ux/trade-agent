/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        trade: {
          50: '#FDF8F3',
          100: '#F9EDE2',
          200: '#F0D6BE',
          300: '#E5B890',
          400: '#D49968',
          500: '#C8A27A',
          600: '#B0805A',
          700: '#8B6346',
          800: '#6B4B35',
          900: '#4A3425',
        },
      },
    },
  },
  plugins: [],
};
