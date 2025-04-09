// Configuration file for PostCSS, used by tools like Tailwind CSS.
module.exports = {
  plugins: {
    // Include Tailwind CSS plugin
    tailwindcss: {},
    // Include Autoprefixer plugin to add vendor prefixes for CSS rules
    // based on browser compatibility data (defined in package.json's browserslist).
    autoprefixer: {},
    // Add other PostCSS plugins here if needed
  },
}