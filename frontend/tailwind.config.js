/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Primary brand ramp — Indigo & Blue (electric/techy, suits lightning theme)
        brand:   { 50:'#E6F1FB', 100:'#B5D4F4', 200:'#85B7EB', 300:'#5BA0E4', 400:'#378ADD', 500:'#185FA5', 600:'#0C447C', 700:'#08365f', 800:'#042C53', 900:'#021c38' },
        // Keep 'rose' as an alias pointing to brand so any leftover refs still render on-theme
        rose:    { 50:'#E6F1FB', 100:'#B5D4F4', 200:'#85B7EB', 300:'#5BA0E4', 400:'#378ADD', 500:'#185FA5', 600:'#0C447C' },
        slate:   { 50:'#f8fafc', 100:'#f1f5f9', 200:'#e2e8f0', 300:'#cbd5e1', 400:'#94a3b8', 500:'#64748b', 600:'#475569', 700:'#334155', 800:'#1e293b', 900:'#0f172a' },
        teal:    { 400:'#2dd4bf', 500:'#14b8a6', 600:'#0d9488' },
        // Status danger ramp
        danger:  { 50:'#FCEBEB', 100:'#F7C1C1', 500:'#E24B4A', 600:'#A32D2D' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0,0,0,0.07), 0 1px 2px -1px rgba(0,0,0,0.07)',
        'card-hover': '0 4px 12px 0 rgba(0,0,0,0.10)',
      }
    },
  },
  plugins: [],
}
