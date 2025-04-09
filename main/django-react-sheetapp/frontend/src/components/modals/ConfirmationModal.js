import React from 'react';
import Modal from '../common/Modal'; // Base modal component
import Button from '../common/Button'; // Reusable button
import LoadingSpinner from '../common/LoadingSpinner'; // Loading indicator

// Generic Confirmation Modal Component
function ConfirmationModal({
    isOpen,                 // Boolean: Controls modal visibility
    onClose,                // Function: Called when modal should close (Escape, backdrop, cancel button)
    onConfirm,              // Function: Called when the confirm button is clicked
    title = "Confirm Action", // String: Title displayed in the modal header
    message = "Are you sure you want to proceed?", // String or ReactNode: Confirmation message/content
    confirmText = "Confirm", // String: Text for the confirmation button
    cancelText = "Cancel",   // String: Text for the cancel button
    isLoading = false,      // Boolean: Shows loading state on confirm button if true
    confirmVariant = "danger" // String: Button variant ('primary', 'danger', 'success', etc.) for confirm action
}) {
    return (
        // Use the base Modal component
        <Modal isOpen={isOpen} onClose={onClose} title={title}>
            {/* Modal Body */}
            <div className="modal-body p-5">
                {/* Display the confirmation message */}
                <p className="text-font-color text-sm md:text-base mb-4">{message}</p>
            </div>
            {/* Modal Footer with Action Buttons */}
            <div className="modal-buttons flex justify-end gap-3 p-4 border-t border-table-border bg-gray-50 dark:bg-gray-800">
                {/* Cancel Button */}
                <Button
                    variant="ghost" // Use ghost variant for cancel
                    size="md"
                    onClick={onClose}
                    disabled={isLoading} // Disable if confirm action is loading
                >
                    {cancelText}
                </Button>
                {/* Confirm Button */}
                <Button
                    variant={confirmVariant} // Use specified variant (e.g., danger for delete)
                    size="md"
                    onClick={onConfirm}
                    isLoading={isLoading} // Show spinner and disable if loading
                    disabled={isLoading}
                    className="min-w-[100px]" // Ensure minimum width to accommodate text/spinner
                >
                    {confirmText}
                </Button>
            </div>
        </Modal>
    );
}

export default ConfirmationModal;