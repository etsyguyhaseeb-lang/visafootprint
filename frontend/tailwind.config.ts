import type { Config } from "tailwindcss";

// Tailwind v4 — most config now lives in app/globals.css via @theme blocks.
// This file is kept for IDE support and any remaining v3-style overrides.
const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
};

export default config;
