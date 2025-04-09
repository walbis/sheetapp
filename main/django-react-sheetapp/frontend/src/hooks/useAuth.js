import { useContext } from 'react';
import AuthContext from '../contexts/AuthContext'; // Import the context object

// Custom hook to simplify accessing the AuthContext.
// Provides type checking and ensures the hook is used within a valid provider.
export const useAuth = () => {
    // Get the context value (which includes user, isAuthenticated, isLoading, login, logout, register)
    const context = useContext(AuthContext);

    // Development check: Ensure the hook is used within the AuthProvider tree.
    // If context is null (the initial value), it means AuthProvider is missing above this component.
    if (context === null) {
        throw new Error("useAuth must be used within an AuthProvider component tree.");
    }

    // Return the context value so components can use { user, login, ... }
    return context;
};