import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "#F4F6F7",
          text: "#111827",
          muted: "#6B7280",
          panel: "#FFFFFF",
          sidebarFrom: "#145A32",
          sidebarVia: "#176C3C",
          sidebarTo: "#1E8449",
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
