import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal'; // Base modal component
import Button from '../common/Button'; // Reusable button
import * as api from '../../services/api'; // API service functions
import LoadingSpinner from '../common/LoadingSpinner'; // Loading indicator
import { useNotification } from '../../hooks/useNotification'; // Hook for notifications
import { useNavigate } from 'react-router-dom'; // Hook for navigation

// Modal for Creating a New ToDo List from a Page
function CreateTodoModal({
    isOpen,           // Boolean: Controls modal visibility
    onClose,          // Function: Called to close the modal
    sourcePageSlug,   // String: Slug of the page this ToDo is based on
    sourcePageName    // String: Name of the source page (for display)
}) {
    const [todoName, setTodoName] = useState('');
    const [isPersonal, setIsPersonal] = useState(true); // Default to personal=true
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({}); // Store errors as object { field: message }
    const { addNotification } = useNotification(); // Get notification function
    const navigate = useNavigate(); // Hook for programmatic navigation

    // Reset form state when modal opens or closes
    useEffect(() => {
        if (isOpen) {
            setTodoName('');
            setIsPersonal(true);
            setErrors({});
            setLoading(false);
        }
    }, [isOpen]);

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault(); // Prevent default form submission
        const trimmedName = todoName.trim();
        if (!trimmedName) {
            setErrors({ name: "ToDo name cannot be empty." });
            return;
        }
        setLoading(true);
        setErrors({}); // Clear previous errors
        console.log("Submitting create ToDo request:", { name: trimmedName, isPersonal, sourcePageSlug });
        try {
            const payload = {
                name: trimmedName,
                is_personal: isPersonal,
                source_page_slug: sourcePageSlug // Pass the source page slug
            };
            const response = await api.createTodo(payload);
            console.log("Create ToDo response:", response.data);
            addNotification(`ToDo list "${response.data.name}" created successfully!`, 'success');
            // Navigate to the newly created ToDo page using its ID (PK)
            navigate(`/todos/${response.data.id}`);
            handleClose(); // Close modal on success
        } catch (err) {
            console.error("Failed to create ToDo:", err.response?.data || err.message);
            // Extract specific error message from backend if available
            const backendErrors = {};
            const errorData = err.response?.data;
            if (errorData && typeof errorData === 'object') {
                 for (const key in errorData) {
                      if (Array.isArray(errorData[key])) {
                          backendErrors[key] = errorData[key].join(' ');
                      } else {
                          backendErrors[key] = errorData[key];
                      }
                 }
                 // Use 'detail' or 'error' as general error if no specific fields match
                 if (Object.keys(backendErrors).length === 0 && (errorData.detail || errorData.error)) {
                      backendErrors.general = errorData.detail || errorData.error;
                 } else if (Object.keys(backendErrors).length === 0) {
                      backendErrors.general = "Failed to create ToDo list. Please try again.";
                 }
            } else {
                 backendErrors.general = "Failed to create ToDo list. An unknown error occurred.";
            }
            setErrors(backendErrors);
            addNotification(backendErrors.general || "Failed to create ToDo list.", 'error');
        } finally {
            setLoading(false); // Ensure loading state is turned off
        }
    };

    // Function to close modal and reset internal state
    const handleClose = () => {
        // Reset state before calling parent's onClose
        setTodoName('');
        setIsPersonal(true);
        setErrors({});
        setLoading(false);
        onClose();
    };

    // Helper to get error message for a specific field
    const getFieldError = (fieldName) => errors?.[fieldName];

    return (
        <Modal
            isOpen={isOpen}
            onClose={handleClose}
            title={sourcePageName ? `Create ToDo from "${sourcePageName}"` : "Create ToDo List"}
        >
            <form onSubmit={handleSubmit}>
                {/* Modal Body */}
                <div className="modal-body p-5 space-y-4">
                    {/* Display general error */}
                    {getFieldError('general') && (
                         <p className="text-red-500 dark:text-red-400 text-sm bg-red-100 dark:bg-red-900 p-2 rounded border border-red-300 dark:border-red-700">
                             {getFieldError('general')}
                         </p>
                     )}
                    {/* ToDo Name Input */}
                    <div>
                        <label htmlFor="todoName" className="block text-sm font-medium text-font-color mb-1">
                            ToDo List Name <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            id="todoName"
                            value={todoName}
                            onChange={(e) => setTodoName(e.target.value)}
                             className={`w-full p-2 border rounded bg-background text-font-color focus:outline-none focus:ring-1 disabled:opacity-50 dark:placeholder-gray-500 ${getFieldError('name') ? 'border-red-500 ring-red-500' : 'border-table-border focus:ring-primary'}`}
                            placeholder="e.g., Sprint Tasks, Bug Fixing"
                            disabled={loading}
                            required
                            maxLength={255}
                            aria-describedby={getFieldError('name') ? "todoName-error" : undefined}
                            aria-invalid={!!getFieldError('name')}
                        />
                        {getFieldError('name') && <p id="todoName-error" className="text-red-500 text-xs mt-1">{getFieldError('name')}</p>}
                    </div>

                    {/* Personal/Public Checkbox */}
                    <div className="flex items-center gap-2 pt-2">
                        <input
                            type="checkbox"
                            id="isPersonal"
                            checked={isPersonal}
                            onChange={(e) => setIsPersonal(e.target.checked)}
                            disabled={loading}
                            className="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-primary focus:ring-primary bg-gray-100 dark:bg-gray-700"
                            aria-describedby="isPersonal-description"
                        />
                        <label htmlFor="isPersonal" className="text-sm text-font-color">
                            Make this ToDo list personal?
                        </label>
                    </div>
                     <p id="isPersonal-description" className="text-xs text-gray-500 dark:text-gray-400 pl-6 -mt-2">
                          If checked, only you (and admins) can view and manage this list. Otherwise, access may depend on the source page's permissions.
                     </p>
                     {getFieldError('is_personal') && <p className="text-red-500 text-xs mt-1">{getFieldError('is_personal')}</p>}
                     {getFieldError('source_page_slug') && <p className="text-red-500 text-xs mt-1">{getFieldError('source_page_slug')}</p>}


                </div>
                {/* Modal Footer */}
                <div className="modal-buttons flex justify-end gap-3 p-4 border-t border-table-border bg-gray-50 dark:bg-gray-800">
                    <Button type="button" variant="ghost" size="md" onClick={handleClose} disabled={loading}>
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        variant="primary"
                        size="md"
                        isLoading={loading}
                        disabled={loading || !todoName.trim()}
                        className="min-w-[120px]" // Adjust min-width as needed
                    >
                        Create ToDo List
                    </Button>
                </div>
            </form>
        </Modal>
    );
}

export default CreateTodoModal;