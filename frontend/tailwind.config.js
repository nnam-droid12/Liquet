/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        liquet: {
          blue: '#2563EB',
          dark: '#1E40AF',
          light: '#DBEAFE',
        },
        liquet_green: '#16A34A',
        liquet_amber: '#D97706',
      },
    },
  },
  plugins: [],
}
