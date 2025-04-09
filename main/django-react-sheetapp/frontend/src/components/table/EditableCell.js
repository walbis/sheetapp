import React, { useState, useEffect, useRef, useCallback } from 'react';

// Represents a single editable cell in the DataTable
function EditableCell({
    initialValue, // The initial value passed from the row data
    isEditing,    // Boolean: Is the table/cell currently in edit mode?
    onSave,       // Callback: (newValue) => void - Called when cell loses focus with changes
    rowIndex,     // Row index (for context/debugging)
    colIndex      // Column index (for context/debugging)
}) {
    // Internal state to manage the current value while editing
    const [value, setValue] = useState(initialValue);
    // Ref to the textarea element for focus management and height calculation
    const textareaRef = useRef(null);

    // Effect to update internal state if the initialValue prop changes from parent
    // This happens on data refresh or when cancelling edits.
    useEffect(() => {
        setValue(initialValue);
    }, [initialValue]);

    // Effect to auto-resize textarea height based on its content when editing
    useEffect(() => {
        if (isEditing && textareaRef.current) {
            textareaRef.current.style.height = 'auto'; // Reset height to recalculate
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`; // Set to content height
        }
    }, [value, isEditing]); // Re-run when value changes or edit mode toggles

    // Callback for handling blur event (losing focus) on the textarea
    const handleBlur = useCallback(() => {
        // Only trigger the onSave callback if the value has actually changed
        if (value !== initialValue) {
            console.log(`Saving cell [${rowIndex}, ${colIndex}]: New='${value}', Old='${initialValue}'`);
            onSave(value); // Call parent's save handler with the new value
        } else {
             // console.log(`Blur cell [${rowIndex}, ${colIndex}]: No change.`);
        }
        // Optionally reset focus state if tracked: setIsFocused(false);
    }, [value, initialValue, rowIndex, colIndex, onSave]); // Dependencies for useCallback

    // Handle changes in the textarea input
    const handleChange = (e) => {
        setValue(e.target.value);
        // Auto-resize is handled by the useEffect hook watching 'value'
    };

    // Handle focus event on the textarea
    const handleFocus = (e) => {
        // Select all text on focus for easier replacement (optional UX)
        e.target.select();
        // Optionally track focus state: setIsFocused(true);
    };

    // Handle keydown events for Enter (save/blur) and Escape (revert/blur)
    const handleKeyDown = (e) => {
        if (!isEditing) return; // Only handle keys when editing

        if (e.key === 'Enter' && !e.shiftKey) { // Enter key (without Shift)
            e.preventDefault(); // Prevent default newline behavior in textarea
            textareaRef.current?.blur(); // Trigger blur, which handles saving if changed
        } else if (e.key === 'Escape') { // Escape key
            e.preventDefault(); // Prevent default browser behavior (like closing modals)
            setValue(initialValue); // Revert internal state to original value
            textareaRef.current?.blur(); // Trigger blur (onSave won't be called as value matches initialValue)
        }
        // TODO: Implement Tab/Shift+Tab navigation between editable cells if desired
        // else if (e.key === 'Tab') { ... handle focus change ... }
    };

    // --- Styling Classes ---
    const commonClasses = "table-cell-bordered p-1 md:p-2 align-top min-h-[40px] h-auto text-left text-font-color transition-colors duration-150";
    // Display mode: allow truncation, show full text on hover (via title)
    const displayClasses = "whitespace-nowrap overflow-hidden text-ellipsis";
    // Editing mode: highlight, allow text wrapping
    const editingClasses = "bg-blue-50 dark:bg-gray-700 outline outline-1 outline-primary";

    return (
        <td
            className={`${commonClasses} ${isEditing ? editingClasses : displayClasses}`}
            data-row={rowIndex}
            data-col={colIndex}
        >
            {isEditing ? (
                // Render textarea when in edit mode
                <textarea
                    ref={textareaRef}
                    className="block w-full h-auto bg-transparent border-none outline-none resize-none p-0 m-0 font-mono text-font-color overflow-hidden leading-snug" // Minimal styling, inherit font
                    value={value}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    onFocus={handleFocus}
                    onKeyDown={handleKeyDown}
                    rows={1} // Start with one row, height adjusts automatically
                    style={{ minHeight: '24px' }} // Ensure a minimum clickable height
                    aria-label={`Edit cell at row ${rowIndex + 1}, column ${colIndex + 1}`} // Accessibility
                />
            ) : (
                 // Render div in display mode
                 <div
                     className="truncate h-full flex items-start pt-0.5" // Align text similar to textarea, allow truncation
                     title={value || '(empty)'} // Show full value on hover
                 >
                    {/* Display value, show placeholder if empty */}
                    {value || <span className="italic text-gray-400 dark:text-gray-500">(empty)</span>}
                 </div>
            )}
        </td>
    );
}

// Memoize the component to prevent re-renders if props haven't changed.
// Crucial for performance in large tables.
export default React.memo(EditableCell);