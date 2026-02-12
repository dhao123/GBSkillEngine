/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#676BEF',
          light: '#E6E9FD',
          dark: '#4F4FF6',
        },
        brand: {
          blue: '#3462FE',
          purple: '#9D34FE',
        },
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: false, // 避免与antd冲突
  },
}
