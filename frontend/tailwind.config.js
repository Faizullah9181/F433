/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // F433 epic color palette
        f433: {
          void: "#050810",
          deep: "#0a0f1a",
          surface: "#0f1629",
          elevated: "#151d2e",
        },
        // Keep stadium colors for backward compatibility
        stadium: {
          navy: "#0a0f1a",
          slate: "#0f1629",
          lime: "#10b981",
          cyan: "#06b6d4",
          rose: "#f43f5e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        float: "float 4s ease-in-out infinite",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(16, 185, 129, 0.3)" },
          "100%": { boxShadow: "0 0 20px rgba(16, 185, 129, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};
