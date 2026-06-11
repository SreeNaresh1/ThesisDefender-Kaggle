import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "var(--ink)",
        slate: "var(--slate)",
        steel: "var(--steel)",
        amber: "var(--amber)",
        ember: "var(--ember)",
        sage: "var(--sage)",
        ghost: "var(--ghost)",
        "warm-white": "var(--warm-white)",
        // Map old variables to new ones to prevent breakage in un-updated components
        background: "var(--ink)",
        "bg-secondary": "var(--slate)",
        "bg-card": "var(--slate)",
        "bg-elevated": "var(--steel)",
        "text-primary": "var(--warm-white)",
        "text-secondary": "var(--ghost)",
        "text-muted": "var(--ghost)",
        border: "var(--steel)",
        "border-hover": "var(--amber)",
        accent: "var(--amber)",
      },
      fontFamily: {
        serif: ["var(--font-dm-serif)"],
        sans: ["var(--font-inter)"],
        mono: ["var(--font-jetbrains-mono)"],
      },
      backgroundImage: {
        'document-grid': 'linear-gradient(to right, var(--steel) 1px, transparent 1px), linear-gradient(to bottom, var(--steel) 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid-sm': '24px 24px',
      },
      animation: {
        'voltage-flicker': 'voltage 0.15s ease-in-out 3',
        'scan-line': 'scan 2s linear infinite',
      },
      keyframes: {
        voltage: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(0.98)' },
          '75%': { opacity: '0.9', transform: 'scale(1.02) skewX(-2deg)' },
        },
        scan: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        }
      }
    },
  },
  plugins: [],
};
export default config;
