import { useContext } from 'react';
import PageActionContext from '../contexts/PageActionContext'; // Import the specific context

// Custom hook to access page-specific actions and states (like editing mode, save handlers).
// Designed to be used primarily by components within the PageView route (e.g., Topbar, DataTable).
export const usePageActions = () => {
    const context = useContext(PageActionContext);

    // This context is expected to be null when the hook is used outside of a
    // route wrapped by PageActionProvider (e.g., on the PageList page).
    // We handle this gracefully by returning a default object with no-op functions
    // or default state values, preventing errors when components try to use the hook elsewhere.
    if (context === null) {
         // console.warn("usePageActions hook used outside of a PageActionProvider. Actions will be disabled.");
         // Return a default object matching the context structure but with safe defaults/no-ops.
         return {
             isEditing: false,
             canEdit: false,
             isLoadingSave: false,
             toggleEdit: () => console.warn("Attempted toggleEdit outside PageActionProvider"),
             addRow: () => console.warn("Attempted addRow outside PageActionProvider"),
             saveChanges: () => console.warn("Attempted saveChanges outside PageActionProvider"),
             cancelEdit: () => console.warn("Attempted cancelEdit outside PageActionProvider"),
             triggerDeletePage: () => console.warn("Attempted triggerDeletePage outside PageActionProvider"),
             triggerCreateTodo: () => console.warn("Attempted triggerCreateTodo outside PageActionProvider"),
             // Add other default no-op functions if actions are added to the context
             registerActions: () => {}, // No-op register function
             updateCanEdit: () => {},   // No-op update function
             updateIsEditing: () => {}, // No-op update function
             updateIsLoadingSave: () => {},// No-op update function
         };
    }

    // If context is not null, return the actual context value provided by PageActionProvider
    return context;
};