/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./template/**/*.{html,js}"],
  theme: {
    extend: {
      colors:{
        'main':'#28C797',
      },
      fontFamily:{
        'quicksand': ['Quicksand']
      }
    },
  },
  plugins: [],
}