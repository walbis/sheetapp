import { useContext } from 'react';
import NotificationContext from '../contexts/NotificationContext'; // Import the context object

// Custom hook to simplify accessing the NotificationContext.
// Provides functions to add and remove notifications.
export const useNotification = () => {
    // Get the context value (which includes notifications, addNotification, removeNotification)
    const context = useContext(NotificationContext);

    // Development check: Ensure the hook is used within the NotificationProvider tree.
    if (context === null) { // Check based on the initial value provided in createContext
        throw new Error("useNotification must be used within a NotificationProvider component tree.");
    }

    // Return the context value
    return context;
};