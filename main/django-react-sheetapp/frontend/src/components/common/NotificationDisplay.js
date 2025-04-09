import React from 'react';
import { useNotification } from '../../hooks/useNotification'; // Hook to access notifications

// Component to display floating notifications
function NotificationDisplay() {
    // Get notifications array and removal function from context
    const { notifications, removeNotification } = useNotification();

    // Don't render the container if there are no notifications
    if (!notifications || notifications.length === 0) {
        return null;
    }

    // Render a container fixed to the top-right corner
    return (
        <div className="fixed top-5 right-5 z-[2000] space-y-2 max-w-sm w-full pointer-events-none">
            {/* Map through notifications and render an item for each */}
            {notifications.map((notification) => (
                <NotificationItem
                    key={notification.id} // Unique key for React list rendering
                    notification={notification}
                    // Pass the remove function with the specific ID bound
                    onDismiss={() => removeNotification(notification.id)}
                />
            ))}
        </div>
    );
}

// Individual notification item component
function NotificationItem({ notification, onDismiss }) {
    // Base styles for all notifications
    const baseStyle = "px-4 py-3 rounded shadow-lg text-sm font-medium flex justify-between items-center animate-slide-in-right pointer-events-auto"; // Allow pointer events on individual items

    // Styles based on notification type (success, error, warning, info)
    const typeStyles = {
        success: "bg-green-500 dark:bg-green-600 text-white",
        error:   "bg-red-600 dark:bg-red-700 text-white",
        warning: "bg-yellow-500 dark:bg-yellow-600 text-black", // Ensure contrast on yellow
        info:    "bg-blue-500 dark:bg-blue-600 text-white",
    };

    // Auto-dismiss timer effect
    React.useEffect(() => {
        // Set a timer to call onDismiss after the specified duration
        const timer = setTimeout(() => {
            onDismiss();
        }, notification.duration || 5000); // Default to 5 seconds if duration not provided

        // Cleanup function: Clear the timer if the component unmounts
        // or if the notification is dismissed manually before the timer fires.
        return () => clearTimeout(timer);
    }, [notification.id, notification.duration, onDismiss]); // Dependencies for the effect


    return (
        <div
            className={`${baseStyle} ${typeStyles[notification.type] || typeStyles.info}`}
            role="alert" // ARIA role for alert messages
            aria-live="assertive" // Announce alerts immediately
        >
            {/* Notification Message */}
            <span>{notification.message}</span>

            {/* Dismiss Button */}
            <button
                onClick={onDismiss}
                className="ml-3 text-lg font-semibold leading-none opacity-70 hover:opacity-100 focus:outline-none focus:ring-1 focus:ring-white rounded-full p-1 -mr-1" // Added focus style
                aria-label="Dismiss notification"
            >
                &times; {/* HTML entity for 'X' */}
            </button>

            {/* Define slide-in animation (can also be in global CSS) */}
            <style>{`
                @keyframes slide-in-right {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                .animate-slide-in-right {
                    animation: slide-in-right 0.3s ease-out forwards;
                }
            `}</style>
        </div>
    );
}


export default NotificationDisplay;