/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Outfit", "system-ui", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
      },
      colors: {
        ink: {
          950: "#07111f",
          900: "#0c1a2e",
          800: "#13233c",
          700: "#1c3350",
        },
        accent: {
          300: "#7ee7d2",
          400: "#3dd6b8",
          500: "#14b8a6",
          600: "#0d9488",
        },
      },
      boxShadow: {
        card: "0 18px 40px -24px rgba(7, 17, 31, 0.45)",
      },
    },
  },
  plugins: [],
};
