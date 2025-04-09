import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal'; // Base modal component
import Button from '../common/Button'; // Reusable button
import * as api from '../../services/api'; // API service functions
import LoadingSpinner from '../common/LoadingSpinner'; // Loading indicator
import { useNotification } from '../../hooks/useNotification'; // Hook for showing notifications

// Modal for Creating a New Page
function CreatePageModal({
    isOpen,         // Boolean: Controls modal visibility
    onClose,        // Function: Called to close the modal
    onPageCreated   // Function: Callback when page is successfully created, passes new page data
}) {
    const [pageName, setPageName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null); // Stores error messages (string or object)
    const { addNotification } = useNotification(); // Get notification function

    // Reset form state when modal opens or closes
    useEffect(() => {
        if (isOpen) {
            setPageName('');
            setError(null);
            setLoading(false);
        }
    }, [isOpen]);

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault(); // Prevent default form submission
        const trimmedName = pageName.trim();
        if (!trimmedName) {
            setError("Page name cannot be empty.");
            return;
        }
        setLoading(true);
        setError(null); // Clear previous errors
        console.log("Submitting create page request:", trimmedName);
        try {
            // Call the API function to create the page
            const response = await api.createPage({ name: trimmedName });
            console.log("Create page response:", response.data);
            // Call the success callback passed from the parent
            if (onPageCreated) {
                onPageCreated(response.data); // Pass back the newly created page object
            }
            handleClose(); // Close modal on success (calls internal reset)
            // Notification is handled by the parent or after navigation usually
        } catch (err) {
            console.error("Failed to create page:", err.response?.data || err.message);
            // Extract specific error message from backend if available
            const backendError = err.response?.data?.name?.[0] // Check for specific field error
                              || err.response?.data?.detail
                              || err.response?.data?.error
                              || "Failed to create page. Please try again.";
            setError(backendError);
            // Show error notification immediately
            addNotification(backendError, 'error');
        } finally {
            setLoading(false); // Ensure loading state is turned off
        }
    };

    // Function to close modal and reset internal state
    const handleClose = () => {
         // Reset state internally before calling parent's onClose
         setPageName('');
         setError(null);
         setLoading(false);
         onClose(); // Call the parent's onClose handler
    }

    // Helper to get specific field error (if backend returns structured errors)
    const getFieldError = (fieldName) => {
        if (error && typeof error === 'object' && error[fieldName]) {
            return Array.isArray(error[fieldName]) ? error[fieldName].join(' ') : error[fieldName];
        }
        // Return general error if error is a string and fieldName is 'name' (common case)
        if (typeof error === 'string' && fieldName === 'name') {
            return error;
        }
        return null;
    };


    return (
        <Modal isOpen={isOpen} onClose={handleClose} title="Create New Page">
            <form onSubmit={handleSubmit}>
                {/* Modal Body */}
                <div className="modal-body p-5">
                    {/* Display general error if error is a string */}
                     {typeof error === 'string' && (
                         <p className="text-red-500 dark:text-red-400 text-sm bg-red-100 dark:bg-red-900 p-2 rounded border border-red-300 dark:border-red-700 mb-3">
                             {error}
                         </p>
                     )}
                    <div className="input-group mb-1">
                         <label htmlFor="pageName" className="block text-sm font-medium text-font-color mb-1">
                             Page Name <span className="text-red-500">*</span>
                         </label>
                        <input
                            type="text"
                            id="pageName"
                            value={pageName}
                            onChange={(e) => setPageName(e.target.value)}
                            // Apply error styling dynamically
                            className={`w-full p-2 border rounded bg-background text-font-color focus:outline-none focus:ring-1 disabled:opacity-50 dark:placeholder-gray-500 ${getFieldError('name') ? 'border-red-500 ring-red-500' : 'border-table-border focus:ring-primary'}`}
                            placeholder="Enter a name for your new page..."
                            disabled={loading}
                            required
                            maxLength={255} // Match model max_length
                            aria-describedby={getFieldError('name') ? "pageName-error" : undefined}
                            aria-invalid={!!getFieldError('name')}
                        />
                        {/* Display field-specific error */}
                         {getFieldError('name') && <p id="pageName-error" className="text-red-500 text-xs mt-1">{getFieldError('name')}</p>}
                    </div>
                </div>
                {/* Modal Footer */}
                <div className="modal-buttons flex justify-end gap-3 p-4 border-t border-table-border bg-gray-50 dark:bg-gray-800">
                    <Button
                        type="button" // Prevent form submission on cancel
                        variant="ghost"
                        size="md"
                        onClick={handleClose}
                        disabled={loading}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        variant="primary"
                        size="md"
                        isLoading={loading} // Pass loading state to button
                        disabled={loading || !pageName.trim()} // Disable if loading or name is empty
                        className="min-w-[100px]"
                    >
                        Create Page
                    </Button>
                </div>
            </form>
        </Modal>
    );
}

export default CreatePageModal;