import React, { useEffect } from 'react';
import ReactDOM from 'react-dom'; // Import ReactDOM for Portal

// Reusable Modal Component using React Portal
function Modal({
    isOpen,        // Boolean to control visibility
    onClose,       // Function to call when closing (backdrop click, Escape key, close button)
    title,         // String for the modal header title
    children,      // Content to render inside the modal body
    size = 'md',   // Size variant: 'sm', 'md', 'lg', 'xl', '2xl'
    closeOnBackdropClick = true, // Allow closing by clicking backdrop
}) {

    // Effect to handle Escape key press for closing the modal
    useEffect(() => {
        const handleEscape = (event) => {
            if (event.key === 'Escape') {
                onClose(); // Call the provided onClose function
            }
        };

        if (isOpen) {
            // Add listener when modal opens
            document.addEventListener('keydown', handleEscape);
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
        } else {
             // Restore body scroll when modal closes
             document.body.style.overflow = '';
        }

        // Cleanup: remove listener and restore scroll when modal closes or component unmounts
        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = ''; // Ensure scroll is restored
        };
    }, [isOpen, onClose]); // Re-run effect if isOpen or onClose changes

    // Don't render anything if the modal is not open
    if (!isOpen) return null;

    // Map size prop to corresponding Tailwind max-width classes
    const sizeClasses = {
        sm: 'max-w-sm',
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl',
         '2xl': 'max-w-2xl', // Example larger size
         'full': 'max-w-full', // Potentially full width
    };

    // Handle backdrop click to close, if enabled
    const handleBackdropClick = () => {
        if (closeOnBackdropClick) {
            onClose();
        }
    };

    // Use React Portal to render the modal outside the main component hierarchy,
    // usually directly into the body, to avoid CSS stacking context issues.
    return ReactDOM.createPortal(
        <div
            className="fixed inset-0 z-[1000] flex items-center justify-center bg-black bg-opacity-60 backdrop-blur-sm p-4 transition-opacity duration-300 ease-out animate-fade-in" // Added fade-in animation
            onClick={handleBackdropClick} // Use handler for backdrop click logic
            role="dialog"           // ARIA role for dialog
            aria-modal="true"       // Indicates it's a modal dialog
            aria-labelledby="modal-title" // Associates title with the dialog
        >
            {/* Modal Content Box */}
            <div
                className={`modal-content bg-background rounded-lg shadow-xl border border-table-border dark:border-primary w-full ${sizeClasses[size]} overflow-hidden flex flex-col max-h-[90vh] transform transition-all duration-300 ease-out scale-95 opacity-0 animate-modal-scale-in`}
                onClick={(e) => e.stopPropagation()} // Prevent click inside content from closing modal
                role="document" // Inner container role
            >
                {/* Modal Header */}
                <div className="modal-header flex justify-between items-center p-4 border-b border-table-border flex-shrink-0 bg-background">
                    {/* Use h2 for semantic modal title */}
                    <h2 id="modal-title" className="text-lg font-bold text-primary truncate pr-2">{title}</h2>
                    {/* Close Button */}
                    <button
                        onClick={onClose}
                        className="modal-close text-font-color opacity-70 hover:opacity-100 hover:text-red-500 text-2xl leading-none font-bold p-1 -m-1 focus:outline-none focus:ring-2 focus:ring-primary rounded-full transition-colors"
                        aria-label="Close modal" // Accessibility label
                    >
                        &times; {/* HTML entity for 'X' */ }
                    </button>
                </div>

                {/* Modal Body/Content - Scrollable */}
                <div className="modal-body-content flex-grow overflow-y-auto">
                    {/* Render children passed to the modal */}
                    {children}
                </div>

            </div>
            {/* Define CSS animations (can also be done in index.css) */}
            <style>{`
                @keyframes modal-fade-in {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .animate-fade-in {
                    animation: modal-fade-in 0.2s ease-out forwards;
                }
                @keyframes modal-scale-in {
                    from { transform: scale(0.95); opacity: 0; }
                    to { transform: scale(1); opacity: 1; }
                }
                .animate-modal-scale-in {
                    animation: modal-scale-in 0.2s ease-out forwards;
                }
            `}</style>
        </div>,
        document.body // Target element for the portal (usually document.body)
    );
}

export default Modal;