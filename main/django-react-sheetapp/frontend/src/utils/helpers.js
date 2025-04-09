// Placeholder for utility functions.

/**
 * Example Utility Function: Format Date
 * Formats a date string or Date object into a more readable format.
 * @param {string | Date} dateInput - The date to format.
 * @param {object} options - Intl.DateTimeFormat options.
 * @returns {string} - Formatted date string or original input on error.
 */
export const formatDate = (dateInput, options = {}) => {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        // hour: '2-digit',
        // minute: '2-digit',
        ...options, // Allow overriding defaults
    };
    try {
        const date = new Date(dateInput);
        // Check if date is valid before formatting
        if (isNaN(date.getTime())) {
             throw new Error("Invalid Date input");
        }
        return new Intl.DateTimeFormat(undefined, defaultOptions).format(date);
    } catch (error) {
        console.error("Error formatting date:", dateInput, error);
        // Return original input or a placeholder on error
        return String(dateInput);
    }
};

/**
 * Example Utility Function: Debounce
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked.
 * @param {Function} func - The function to debounce.
 * @param {number} wait - The number of milliseconds to delay.
 * @returns {Function} - The new debounced function.
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func.apply(this, args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Add other utility functions as needed (e.g., throttle, deepClone, validation helpers)