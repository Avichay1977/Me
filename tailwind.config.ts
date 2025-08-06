import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
      },
      colors: {
        'brand-blue': '#3b82f6',
        'brand-green': '#10b981',
        'brand-red': '#ef4444',
        'brand-yellow': '#f59e0b',
        'dark-bg': '#111827',
        'dark-card': '#1f2937',
        'dark-border': '#374151',
      }
    },
  },
  plugins: [
    function ({ addUtilities }: { addUtilities: any }) {
      addUtilities({
        '.custom-scrollbar': {
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#1f2937',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#4b5563',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#6b7280',
          },
        },
      });
    },
  ],
};
export default config;
