import React, { createContext, useState, useCallback, useMemo } from 'react';

// This context provides state and actions specific to the PageView component.
// It allows components like Topbar or nested buttons within PageView
// to trigger actions (like save, add row) and know the editing state.

const PageActionContext = createContext(null); // Initialize with null

export const PageActionProvider = ({ children }) => {
    // State managed by this context, controllable by the PageView component
    const [isEditing, setIsEditing] = useState(false);
    const [canEdit, setCanEdit] = useState(false); // Does the user have permission to edit this page?
    const [isLoadingSave, setIsLoadingSave] = useState(false); // Is a save operation currently in progress?

    // Placeholder object for action functions - PageView will provide the actual implementations
    const [actions, setActions] = useState({
        toggleEdit: () => console.warn("PageActionContext: toggleEdit action not yet registered."),
        addRow: () => console.warn("PageActionContext: addRow action not yet registered."),
        saveChanges: () => console.warn("PageActionContext: saveChanges action not yet registered."),
        cancelEdit: () => console.warn("PageActionContext: cancelEdit action not yet registered."),
        triggerDeletePage: () => console.warn("PageActionContext: triggerDeletePage action not yet registered."),
        triggerCreateTodo: () => console.warn("PageActionContext: triggerCreateTodo action not yet registered."),
        // Define placeholders for other actions if needed (e.g., add/delete column)
        // addColumn: () => console.warn("PageActionContext: addColumn action not yet registered."),
        // deleteColumn: (colId) => console.warn("PageActionContext: deleteColumn action not yet registered."),
        // deleteRow: (rowId) => console.warn("PageActionContext: deleteRow action not yet registered."),
    });

    // Function for the PageView component to call to provide its action implementations
    const registerActions = useCallback((actionImpls) => {
        // Merge provided implementations with existing actions (or defaults)
        setActions(prev => ({ ...prev, ...actionImpls }));
        console.log("PageActionContext: Actions registered.");
    }, []); // This function itself is stable

    // Functions for PageView to update the context's state
    const updateCanEdit = useCallback((canUserEdit) => {
        setCanEdit(canUserEdit);
        // console.log("PageActionContext: canEdit updated to", canUserEdit);
    }, []);

    const updateIsEditing = useCallback((editingStatus) => {
        setIsEditing(editingStatus);
        // console.log("PageActionContext: isEditing updated to", editingStatus);
    }, []);

    const updateIsLoadingSave = useCallback((loadingStatus) => {
        setIsLoadingSave(loadingStatus);
        // console.log("PageActionContext: isLoadingSave updated to", loadingStatus);
    }, []);

    // Memoize the context value to optimize performance
    // The context value includes state and functions to update state/register actions
    const contextValue = useMemo(() => ({
        isEditing,
        canEdit,
        isLoadingSave,
        ...actions, // Spread the registered action functions
        registerActions, // Function to register actions
        updateCanEdit,   // Function to update edit permission state
        updateIsEditing, // Function to update editing mode state
        updateIsLoadingSave, // Function to update save loading state
    }), [
        isEditing, canEdit, isLoadingSave, actions, registerActions,
        updateCanEdit, updateIsEditing, updateIsLoadingSave
    ]); // Dependencies ensure value updates when state or registered actions change

    return (
        <PageActionContext.Provider value={contextValue}>
            {children}
        </PageActionContext.Provider>
    );
};

export default PageActionContext;