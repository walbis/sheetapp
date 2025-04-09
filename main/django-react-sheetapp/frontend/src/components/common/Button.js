import React from 'react';
import LoadingSpinner from './LoadingSpinner'; // Import spinner

// Reusable button component with variants and loading state
function Button({
    children,
    onClick,
    type = 'button',
    variant = 'primary', // e.g., primary, secondary, danger, warning, success, ghost, link
    size = 'md', // e.g., sm, md, lg
    disabled = false,
    isLoading = false, // Add loading state
    className = '', // Allow passing additional custom classes
    ...props // Spread other props like title, aria-label etc.
}) {
    // Base styles applicable to all buttons
    const baseStyles = "font-bold rounded-full text-sm shadow-sm transition duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2";

    // Size specific styles
    const sizeStyles = {
        sm: 'py-1 px-3 text-xs',
        md: 'py-2 px-4 text-sm',
        lg: 'py-2.5 px-6 text-base',
    };

    // Variant specific styles
    const variantStyles = {
        primary: 'bg-primary hover:opacity-90 text-white focus:ring-primary',
        secondary: 'bg-gray-500 hover:bg-gray-600 text-white focus:ring-gray-500',
        danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-600',
        warning: 'bg-yellow-500 hover:bg-yellow-600 text-gray-900 focus:ring-yellow-500', // Text color contrast
        success: 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-600',
        ghost: 'bg-transparent hover:bg-hover-bg text-font-color border border-table-border focus:ring-primary',
        link: 'bg-transparent hover:underline text-link-color p-0 shadow-none focus:ring-link-color text-sm', // Link style
    };

    // Combine all classes
    const combinedClassName = `${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`;

    // Determine if the button should be disabled (explicitly or due to loading)
    const isDisabled = disabled || isLoading;

    return (
        <button
            type={type}
            onClick={onClick}
            disabled={isDisabled}
            className={combinedClassName}
            {...props}
        >
            {/* Show loading spinner if isLoading */}
            {isLoading && <LoadingSpinner size="sm" color={variant === 'warning' || variant === 'ghost' || variant === 'link' ? 'text-font-color' : 'text-white'} />}
            {/* Render children (button text or icons) */}
            <span>{children}</span>
        </button>
    );
}

export default Button;