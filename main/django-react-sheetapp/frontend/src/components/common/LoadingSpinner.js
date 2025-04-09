import React from 'react';

// Simple SVG Spinner Component
// Props:
// - size: 'sm', 'md', 'lg' (default: 'md')
// - color: Tailwind text color class (default: 'text-primary')
// - className: Additional CSS classes
function LoadingSpinner({ size = 'md', color = 'text-primary', className = '' }) {
    // Map size prop to Tailwind height/width classes
    const sizeClasses = {
        sm: 'h-4 w-4',
        md: 'h-6 w-6',
        lg: 'h-8 w-8',
    };

    return (
        <svg
            className={`animate-spin ${sizeClasses[size]} ${color} ${className}`}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            role="status" // Indicate role for accessibility
            aria-live="polite" // Announce changes if content updates (though usually static)
        >
             <title>Loading...</title> {/* Accessible title */}
            <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                aria-hidden="true" // Hide decorative parts from screen reader
            ></circle>
            <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                aria-hidden="true"
            ></path>
        </svg>
    );
}

export default LoadingSpinner;