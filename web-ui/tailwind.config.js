/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0077B6',   // Bright Teal Blue (Agentic Core)
        secondary: '#00AFB9', // Vibrant Seafoam (Success)
        accent: '#48CAE4',    // Sky Aqua (Reasoning Glows)
        danger: '#F07167',    // Soft Coral (Alerts)
        edu: {
          bg: {
            dark: '#121212',  // Midnight Obsidian
            light: '#F5FBFE'
          },
          surface: {
            dark: '#1E293B',  // Slate widget surface
            light: '#FFFFFF'
          },
          text: {
            dark: '#CAF0F8',  // Light Cyan
            light: '#03045E'  // Deep Twilight
          },
          border: {
            ocean: '#90E0EF'  // Frosted Blue
          }
        }
      }
    },
  },
  plugins: [],
}
