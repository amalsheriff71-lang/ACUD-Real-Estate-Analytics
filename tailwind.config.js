/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1D1616",
        maroon: "#8E1616",
        signal: "#D84040",
        mist: "#EEEEEE"
      },
      boxShadow: {
        soft: "0 18px 50px rgba(29, 22, 22, 0.08)"
      }
    },
  },
  plugins: [],
};
