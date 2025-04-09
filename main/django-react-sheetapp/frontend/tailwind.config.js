/** @type {import('tailwindcss').Config} */
module.exports = {
  // Enable dark mode using the 'class' strategy (requires setting class="dark" on html/body)
  // Our ThemeContext handles adding/removing the 'dark' class based on the 'data-theme' attribute logic.
  // Alternatively, use 'media' strategy for OS-level dark mode preference.
  darkMode: 'class', // Use data-theme attribute selector defined in index.css via ThemeContext
  // Configure paths to all template files where Tailwind class names will be used.
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // Scan JavaScript and TypeScript files in src/
    "./public/index.html", // Scan the main HTML file if classes are used there
  ],
  theme: {
    // Extend the default Tailwind theme
    extend: {
      // Define custom font families
      fontFamily: {
        // Set Roboto Mono as the primary monospace font, falling back to generic monospace
        mono: ['"Roboto Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
        // Optionally define a sans-serif font if needed for other elements
        // sans: ['Inter', 'ui-sans-serif', 'system-ui', ...],
      },
      // Define custom colors using CSS variables for easy theming
      colors: {
        // Use CSS variable names defined in src/styles/index.css
        primary: 'var(--main-color)',
        background: 'var(--bg-color)',
        'font-color': 'var(--font-color)',
        'hover-bg': 'var(--hover-bg)',
        'link-color': 'var(--link-color)',
        // Define status colors using CSS variables
        'status-not-started': 'var(--status-not-started)',
        'status-in-progress': 'var(--status-in-progress)',
        'status-completed': 'var(--status-completed)',
      },
      // Define custom border colors using CSS variables
      borderColor: {
         DEFAULT: 'var(--table-border-color)', // Set default border color for 'border' utility
         table: 'var(--table-border-color)', // Explicit name for table borders
         primary: 'var(--main-color)', // Allow bordering with primary color
      },
       // Define custom border widths using CSS variables
       borderWidth: {
         DEFAULT: 'var(--border-size)', // Set default border width for 'border' utility
         table: 'var(--border-size)', // Explicit name for table borders/cells
         '0': '0',
         '2': '2px', // Keep standard options if needed
         '4': '4px',
         '8': '8px',
      },
      // Define custom ring colors (for focus outlines)
      ringColor: {
          primary: 'var(--main-color)',
      },
      // Define ring offset color based on background
       ringOffsetColor: {
           background: 'var(--bg-color)',
       },
       // Add custom animations if needed
       keyframes: {
           'fade-in': {
               '0%': { opacity: '0' },
               '100%': { opacity: '1' },
           },
           'scale-in': {
                '0%': { opacity: '0', transform: 'scale(0.95)' },
                '100%': { opacity: '1', transform: 'scale(1)' },
            },
           'slide-in-right': {
                '0%': { opacity: '0', transform: 'translateX(100%)' },
                '100%': { opacity: '1', transform: 'translateX(0)' },
            },
       },
        animation: {
            'fade-in': 'fade-in 0.2s ease-out forwards',
            'modal-scale-in': 'scale-in 0.2s ease-out forwards',
            'slide-in-right': 'slide-in-right 0.3s ease-out forwards',
        },
    },
  },
  // Add Tailwind plugins
  plugins: [
     require('@tailwindcss/forms'), // Optional plugin for better default form styling
     // Add other plugins like aspect-ratio, typography if needed
  ],
}