import React, { createContext, useState, useEffect, useMemo, useCallback } from 'react';

// Create the context object
const ThemeContext = createContext(null); // Initialize with null

// Create the provider component
export const ThemeProvider = ({ children }) => {
  // State for the current theme ('light' or 'dark')
  // Initialize theme from localStorage or default to 'light'
  const [theme, setTheme] = useState(() => {
      try {
         // Attempt to read saved theme preference
         const savedTheme = localStorage.getItem('theme');
         // Return saved theme only if it's valid ('light' or 'dark'), otherwise default
         return savedTheme && (savedTheme === 'light' || savedTheme === 'dark') ? savedTheme : 'light';
      } catch (error) {
         // Handle potential errors reading localStorage (e.g., security restrictions)
         console.error("Error reading theme from localStorage:", error);
         return 'light'; // Default theme on error
      }
  });

  // State for party mode activation
  const [partyModeActive, setPartyModeActive] = useState(false);
  // State to store the interval ID for party mode timer
  const [partyIntervalId, setPartyIntervalId] = useState(null);

  // Effect runs when 'theme' state changes:
  // - Applies the current theme to the root HTML element (for CSS variable switching)
  // - Saves the current theme preference to localStorage
  useEffect(() => {
    // Set data attribute on root element
    document.documentElement.setAttribute('data-theme', theme);
    try {
         // Persist theme choice
         localStorage.setItem('theme', theme);
    } catch (error) {
         console.error("Error saving theme to localStorage:", error);
    }
     // console.log("Theme applied and saved:", theme); // Debug log
  }, [theme]); // Dependency: runs only when theme changes

  // Function to toggle theme manually (light <-> dark)
  // useCallback ensures the function reference remains stable
  const toggleTheme = useCallback(() => {
    // If party mode is currently active, turn it off before manually toggling
    if (partyModeActive) {
        // We need access to the togglePartyMode function here.
        // This indicates a potential need to rethink dependencies or how state is managed.
        // For now, assume togglePartyMode defined below can be called.
        // It might be better to pass the clearInterval logic directly here or manage
        // party mode state more centrally if this dependency becomes problematic.
        if (partyIntervalId) {
            clearInterval(partyIntervalId);
            setPartyIntervalId(null);
        }
        setPartyModeActive(false); // Ensure party mode state is off
        console.log("Party mode stopped due to manual theme toggle.");
    }
    // Toggle the theme state
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
  }, [partyModeActive, partyIntervalId]); // Dependency: need partyModeActive to decide whether to stop interval

  // Function to toggle party mode on/off
  // useCallback ensures the function reference remains stable
  const togglePartyMode = useCallback(() => {
    setPartyModeActive(prevActive => {
        const nextActive = !prevActive; // Determine the next state
        if (nextActive) {
            // --- Starting Party Mode ---
            console.log("Party mode activating!");
            // Set up an interval timer to toggle the theme rapidly
            const intervalId = setInterval(() => {
                // Use functional update to toggle based on the *latest* theme state
                setTheme((currentTheme) => (currentTheme === 'light' ? 'dark' : 'light'));
            }, 150); // Interval duration in milliseconds
            setPartyIntervalId(intervalId); // Store the interval ID so we can clear it later
        } else {
             // --- Stopping Party Mode ---
             console.log("Party mode deactivating.");
             // Clear the interval timer if it exists
             if (partyIntervalId) {
                 clearInterval(partyIntervalId);
                 setPartyIntervalId(null); // Reset the stored interval ID
             }
             // Optional: Restore the theme to its state before party mode started?
             // Or just leave it as the last theme set by the interval.
             // To restore:
             // try {
             //    const savedTheme = localStorage.getItem('theme') || 'light';
             //    setTheme(savedTheme);
             // } catch (error) { setTheme('light'); }
        }
        return nextActive; // Return the new active state
    });
  }, [partyIntervalId]); // Dependency: need partyIntervalId to clear it correctly

  // Memoize the context value object to optimize performance.
  // This object will only be recreated if one of its dependencies changes.
  const value = useMemo(() => ({
      theme,            // Current theme state ('light' or 'dark')
      toggleTheme,      // Function to manually toggle theme
      partyModeActive,  // Boolean: Is party mode currently active?
      togglePartyMode   // Function to toggle party mode on/off
     }),
    [theme, toggleTheme, partyModeActive, togglePartyMode] // Dependencies for useMemo
   );

  // Provide the context value to all child components
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeContext;