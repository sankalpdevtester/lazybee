/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bee: {
          yellow: '#F5C518',
          dark: '#0D0D0D',
          card: '#141414',
          border: '#1F1F1F',
          muted: '#6B7280',
        }
      }
    }
  },
  plugins: []
}
