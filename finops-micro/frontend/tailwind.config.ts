import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "#F6F7F9",
          text: "#111827",
          muted: "#374151",
          panel: "#FFFFFF",
          sidebarFrom: "#0B5A3C",
          sidebarVia: "#0F6A44",
          sidebarTo: "#128055",
          selected: "#E9F8EF",
        },
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
      },
      boxShadow: {
        soft: "0 8px 20px rgba(17,24,39,0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
