import React, { createContext, useState, useEffect, useCallback, useMemo } from 'react';
import api from '../services/api'; // Import configured axios instance

// Create Context object
const AuthContext = createContext(null); // Initialize with null

// Create Provider component
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true); // Start in loading state

    // Function to check authentication status with backend
    const checkAuthStatus = useCallback(async () => {
        console.log("Checking auth status...");
        setIsLoading(true);
        try {
            // No need to fetch CSRF here, GET requests don't require it,
            // and subsequent POSTs will fetch it via interceptor if needed.
            // The /auth/status endpoint relies on the session cookie being sent.
            const response = await api.get('/auth/status/');
            if (response.status === 200 && response.data.isAuthenticated) {
                console.log("User IS authenticated:", response.data.user.email);
                setUser(response.data.user);
                setIsAuthenticated(true);
            } else {
                console.log("User is NOT authenticated.");
                setUser(null);
                setIsAuthenticated(false);
            }
        } catch (error) {
            // Treat errors (like 401/403 from expired session, or network errors) as not authenticated
            console.error("Auth status check failed:", error.response?.status, error.message);
            setUser(null);
            setIsAuthenticated(false);
        } finally {
            // Only set loading to false *after* the check is complete
            setIsLoading(false);
            console.log("Auth status check finished. isLoading:", false);
        }
    }, []);

    // Run auth check on initial mount
    useEffect(() => {
        checkAuthStatus();
    }, [checkAuthStatus]);

    // --- Authentication Actions ---

    const login = async (email, password) => {
        console.log("AuthContext: Attempting login...");
        setIsLoading(true); // Indicate loading during login process
        try {
            // Login API call (POST request needs CSRF handling via interceptor)
            const response = await api.post('/auth/login/', { email, password });
            // Assuming successful login returns user data and sets session cookie
            console.log("AuthContext: Login API success", response.data);
            setUser(response.data);
            setIsAuthenticated(true);
            setIsLoading(false);
            return { success: true, user: response.data };
        } catch (error) {
            console.error("AuthContext: Login failed", error.response?.data || error.message);
            setUser(null);
            setIsAuthenticated(false);
            setIsLoading(false);
             // Return structured error
             return { success: false, error: error.response?.data?.error || "Login failed" };
        }
    };

    const register = async (username, email, password, password2) => {
         console.log("AuthContext: Attempting registration...");
         setIsLoading(true);
        try {
            // Register API call (POST request needs CSRF handling via interceptor)
            const response = await api.post('/auth/register/', { username, email, password, password2 });
            console.log("AuthContext: Register API success", response.data);
            // Registration successful, but user is NOT logged in automatically
            setIsLoading(false);
            return { success: true, user: response.data }; // Return user data but don't set auth state
        } catch (error) {
            console.error("AuthContext: Registration failed", error.response?.data || error.message);
            setIsLoading(false);
            // Return structured error from backend if available
             return { success: false, error: error.response?.data || { detail: "Registration failed" } };
        }
    };

    const logout = async () => {
        const userEmail = user?.email || 'Unknown User'; // Get email before clearing state
        console.log(`AuthContext: Attempting logout for ${userEmail}...`);
        setIsLoading(true);
        try {
            // Logout API call (POST request needs CSRF handling via interceptor)
            await api.post('/auth/logout/');
            console.log("AuthContext: Logout API success");
        } catch (error) {
            console.error("AuthContext: Logout API call failed", error.response?.data || error.message);
            // Log error but proceed with client-side cleanup regardless
        } finally {
             // Clear client-side state regardless of API call success/failure
            setUser(null);
            setIsAuthenticated(false);
            setIsLoading(false);
            console.log("AuthContext: Client-side logout complete.");
            // Navigation should happen in the component calling logout or via route checks
        }
    };

    // Memoize the context value to prevent unnecessary re-renders of consumers
    // Ensure callback functions have stable references if they don't depend on changing state other than via `set`ters
    const contextValue = useMemo(() => ({
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        register,
        checkAuthStatus // Expose checkAuthStatus if needed for manual refresh
    }), [user, isAuthenticated, isLoading, checkAuthStatus]); // Add login, logout, register if needed (they are stable refs due to useCallback pattern usually implicitly used by useState setters)

    // Provide the context value to children components
    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;