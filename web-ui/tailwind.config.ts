import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(214 32% 91%)",
        background: "hsl(0 0% 100%)",
        foreground: "hsl(222 47% 11%)",
        primary: { DEFAULT: "hsl(222 47% 11%)", foreground: "hsl(0 0% 100%)" },
        muted: { DEFAULT: "hsl(210 40% 96%)", foreground: "hsl(215 16% 47%)" },
        destructive: { DEFAULT: "hsl(0 84% 60%)", foreground: "hsl(0 0% 100%)" },
      },
    },
  },
  plugins: [],
};

export default config;
