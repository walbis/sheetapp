import React from 'react';

// Define status choices with labels and associated Tailwind color classes
const STATUS_CHOICES = [
    { value: 'NOT_STARTED', label: 'Not Started', colorClass: 'text-status-not-started' },
    { value: 'IN_PROGRESS', label: 'In Progress', colorClass: 'text-status-in-progress' },
    { value: 'COMPLETED', label: 'Completed',   colorClass: 'text-status-completed' },
];

// Component for the dropdown status selector in ToDo tables
function StatusSelect({
    currentStatus, // The current status value (e.g., 'NOT_STARTED')
    rowId,         // The unique ID of the row this status belongs to
    onStatusChange,// Callback function: (rowId, newStatus) => void
    disabled = false // Optional: disable the select input
}) {

    // Handle change event on the select element
    const handleChange = (e) => {
        const newStatus = e.target.value;
        // Call the parent's handler function with the row ID and the new status value
        if (onStatusChange) {
            onStatusChange(rowId, newStatus);
        } else {
             console.warn("StatusSelect: onStatusChange handler not provided!");
        }
    };

    // Find the color class corresponding to the currently selected status
    const currentColorClass = STATUS_CHOICES.find(s => s.value === currentStatus)?.colorClass
                              || 'text-font-color'; // Default color if status not found

    return (
        <select
            value={currentStatus} // Control the selected option
            onChange={handleChange}
            disabled={disabled}
            // Apply base styles + dynamic color class for the selected text
            className={`status-select w-full h-full p-1 border-none bg-transparent font-mono appearance-none cursor-pointer font-bold text-sm focus:outline-none focus:ring-1 focus:ring-primary ${currentColorClass}`}
            aria-label={`Status for item ${rowId}`} // Accessibility label
        >
            {/* Map through the choices to render options */}
            {STATUS_CHOICES.map(statusOption => (
                <option
                    key={statusOption.value}
                    value={statusOption.value}
                    // Apply specific styling to options if needed (browser support varies)
                    // Note: Direct option styling might not inherit the select's text color easily.
                    // The select's text color changes based on the *selected* value.
                    className="bg-background text-font-color font-mono font-normal" // Basic option styling
                >
                    {statusOption.label}
                </option>
            ))}
        </select>
    );
}

// Memoize for performance, especially if used in many rows
export default React.memo(StatusSelect);