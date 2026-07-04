import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["var(--font-sans)", "system-ui", "sans-serif"] },
      colors: {
        ink: { DEFAULT: "#0a0a0f", 800: "#12121a", 700: "#1a1a26", 600: "#242435" },
        accent: { DEFAULT: "#6366f1", glow: "#818cf8" },
        cyan: { DEFAULT: "#22d3ee" },
      },
      keyframes: {
        "fade-up": { "0%": { opacity: "0", transform: "translateY(8px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        "pulse-ring": { "0%,100%": { opacity: "0.4" }, "50%": { opacity: "1" } },
      },
      animation: { "fade-up": "fade-up 0.4s ease-out", "pulse-ring": "pulse-ring 1.6s ease-in-out infinite" },
    },
  },
  plugins: [],
};
export default config;
