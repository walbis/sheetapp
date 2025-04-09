import React, { createContext, useState, useCallback, useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid'; // Library to generate unique IDs

// Create the context object
const NotificationContext = createContext(null); // Initialize with null

// Create the provider component
export const NotificationProvider = ({ children }) => {
    // State to hold the array of current notifications
    const [notifications, setNotifications] = useState([]);

    // Function to add a new notification
    // useCallback ensures this function reference is stable unless dependencies change
    const addNotification = useCallback((
        message,                 // The message string to display
        type = 'info',         // Type of notification ('info', 'success', 'warning', 'error')
        duration = 5000        // Duration in milliseconds before auto-dismiss (default 5s)
    ) => {
        const id = uuidv4(); // Generate a unique ID for this notification
        const newNotification = { id, message, type, duration };

        // Add the new notification to the beginning of the array (newest first)
        setNotifications(prevNotifications => [newNotification, ...prevNotifications]);
        console.log("Added notification:", newNotification);

        // Optional: Limit the number of displayed notifications
        // setNotifications(prev => [newNotification, ...prev].slice(0, 5)); // Keep only latest 5
    }, []); // No dependencies, function is stable

    // Function to remove a notification by its ID
    // useCallback ensures this function reference is stable
    const removeNotification = useCallback((idToRemove) => {
        // Filter out the notification with the matching ID
        setNotifications(prevNotifications =>
            prevNotifications.filter(notification => notification.id !== idToRemove)
        );
         console.log("Removed notification:", idToRemove);
    }, []); // No dependencies, function is stable

    // Memoize the context value to prevent unnecessary re-renders in consuming components
    // The value object only changes if the notifications array itself changes
    const contextValue = useMemo(() => ({
        notifications,
        addNotification,
        removeNotification,
    }), [notifications, addNotification, removeNotification]); // Include callbacks in dependencies

    // Provide the context value to children components
    return (
        <NotificationContext.Provider value={contextValue}>
            {children}
        </NotificationContext.Provider>
    );
};

export default NotificationContext;