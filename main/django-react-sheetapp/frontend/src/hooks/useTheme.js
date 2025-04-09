import { useContext } from 'react';
import ThemeContext from '../contexts/ThemeContext'; // Import the context object

// Custom hook to simplify accessing the ThemeContext.
// Provides access to the current theme and functions to toggle theme/party mode.
export const useTheme = () => {
    // Get the context value (which includes theme, toggleTheme, partyModeActive, togglePartyMode)
    const context = useContext(ThemeContext);

    // Development check: Ensure the hook is used within the ThemeProvider tree.
    if (context === null) { // Check based on the initial value provided in createContext
        throw new Error("useTheme must be used within a ThemeProvider component tree.");
    }

    // Return the context value
    return context;
};