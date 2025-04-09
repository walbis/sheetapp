import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DataTable from '../components/table/DataTable'; // The main table component
import LoadingSpinner from '../components/common/LoadingSpinner';
import ConfirmationModal from '../components/modals/ConfirmationModal';
import CreateTodoModal from '../components/modals/CreateTodoModal';
import Button from '../components/common/Button'; // Reusable button
import * as api from '../services/api'; // API service functions
import { useNotification } from '../hooks/useNotification'; // Hook for notifications
import { usePageActions } from '../hooks/usePageActions'; // Hook for page state/actions context

// Component to display and edit a single page
function PageView() {
    const { pageSlug } = useParams(); // Get page slug from URL
    const navigate = useNavigate(); // Hook for navigation
    const { addNotification } = useNotification(); // Hook for displaying notifications

    // --- Local State ---
    const [pageData, setPageData] = useState(null); // Holds fetched, canonical data (columns, rows, owner etc.)
    const [editData, setEditData] = useState(null); // Holds data currently being modified in edit mode
    const [loading, setLoading] = useState(true);   // Loading state for initial data fetch
    const [pageError, setPageError] = useState(null); // Error during page fetch/access
    const [editError, setEditError] = useState(null); // Error during save operation
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false); // Control delete confirmation modal
    const [showCreateTodoModal, setShowCreateTodoModal] = useState(false); // Control create ToDo modal
    const [isDeleting, setIsDeleting] = useState(false); // Loading state for delete operation

    // --- Context State and Actions ---
    const {
        isEditing,             // Is the page currently in edit mode? (from context)
        canEdit,               // Does the user have permission to edit? (from context)
        isLoadingSave,         // Is a save operation currently running? (from context)
        registerActions,       // Function to register this component's actions with the context
        updateCanEdit,         // Function to update context's 'canEdit' state
        updateIsEditing,       // Function to update context's 'isEditing' state
        updateIsLoadingSave,   // Function to update context's 'isLoadingSave' state
     } = usePageActions();

     // --- Ref for Mount Status ---
     const isMounted = useRef(true);
     useEffect(() => {
          isMounted.current = true; // Set to true when component mounts
          return () => { isMounted.current = false; }; // Set to false when component unmounts
      }, []);


    // --- Data Fetching Logic ---
    // Define fetchData using useCallback to memoize it
    const fetchData = useCallback(async (abortController) => {
         console.log(`PageView: Fetching data for page: ${pageSlug}`);
         if (!isMounted.current) return;
        setLoading(true);
        setPageError(null);
        // Clear edit errors on fresh fetch, but maybe preserve if fetch follows failed save? Decision needed.
        // setEditError(null);
        try {
            const response = await api.getPageData(pageSlug, { signal: abortController?.signal });
            if (!isMounted.current) return; // Check again after await

            const fetchedData = response.data;
            setPageData(fetchedData);

            // TODO: Replace placeholder with actual permission check logic if needed frontend-side
            const canUserEdit = true; // Placeholder - Rely on backend API permissions for now
            updateCanEdit(canUserEdit); // Update context

            // Initialize or reset editData based on the fetched canonical data
            setEditData(JSON.parse(JSON.stringify(fetchedData))); // Deep copy
            console.log("PageView: Data fetched successfully:", fetchedData);

        } catch (err) {
            if (err.name === 'CanceledError') {
                 console.log("PageView: Fetch aborted");
                 return;
            }
            console.error("PageView: Failed to fetch page data:", err.response?.data || err.message);
            if (!isMounted.current) return;

            const errorMsg = err.response?.data?.detail || err.response?.data?.error || "Could not load page data.";
            setPageError(errorMsg);
            addNotification(errorMsg, 'error');
            if (err.response?.status === 404) setPageError("Page not found.");
            if (err.response?.status === 403) {
                 setPageError("You do not have permission to view this page.");
                 updateCanEdit(false); // Ensure context reflects lack of permission
            }
        } finally {
             if (isMounted.current) setLoading(false);
        }
    // updateCanEdit and addNotification are stable refs from context/hooks
    }, [pageSlug, updateCanEdit, addNotification]);

    // Fetch data on initial load and when pageSlug changes
    useEffect(() => {
         const abortController = new AbortController();
         fetchData(abortController);
         return () => {
             console.log("PageView: Aborting fetch on unmount/slug change");
             abortController.abort();
         };
    }, [fetchData]); // fetchData includes pageSlug as dependency


    // --- Action Handlers (Defined with useCallback) ---
    // Define dependent functions (like handleSaveChanges) BEFORE functions that use them.

    const handleSaveChanges = useCallback(async () => {
         if (!isEditing || !editData) {
             console.warn("Save called but not in editing mode or no edit data.");
             return; // Should not happen if logic is correct
         }
         console.log("PageView: Attempting to save changes...");
         updateIsLoadingSave(true); // Update context state
         setEditError(null);
         try {
            // Prepare payload, ensuring IDs are null for new items
            const payload = {
                 columns: editData.columns.map(col => ({
                     id: col.id || null,
                     name: col.name,
                     order: col.order,
                     width: col.width,
                 })),
                 rows: editData.rows.map(row => ({
                      id: row.id || null,
                      order: row.order,
                      cells: row.cells,
                 })),
                 // commit_message: "Frontend Save" // Optional
            };
            await api.savePageData(pageSlug, payload);
             if (!isMounted.current) return;

            addNotification("Page saved successfully!", 'success');
            updateIsEditing(false); // Exit edit mode in context
            await fetchData(); // Re-fetch canonical data after successful save
         } catch (err) {
             console.error("PageView: Failed to save page data:", err.response?.data || err.message);
             if (!isMounted.current) return;

             const errorData = err.response?.data;
             let errorMsg = "Failed to save changes.";
             // Extract more specific error if possible
             if (typeof errorData === 'object' && errorData !== null) {
                 const messages = Object.values(errorData).flat().filter(msg => typeof msg === 'string');
                 if (messages.length > 0) errorMsg = messages.join(' ');
                 else if (errorData.detail || errorData.error) errorMsg = errorData.detail || errorData.error;
             } else if (typeof errorData === 'string') errorMsg = errorData;

             setEditError(errorMsg); // Set local error state
             addNotification(errorMsg, 'error');
             // Keep editing mode active on error
         } finally {
              if (isMounted.current) updateIsLoadingSave(false); // Update context state
         }
    // Dependencies: Include all external variables/state/functions used inside
    }, [isEditing, editData, pageSlug, fetchData, updateIsEditing, updateIsLoadingSave, addNotification]);


    const handleToggleEdit = useCallback(() => {
        setEditError(null); // Clear previous save errors
        if (isEditing) {
            // If currently editing, attempt to save changes
            handleSaveChanges(); // <<<<<<<<<<<<<<<< CALL handleSaveChanges HERE
        } else {
            // Entering edit mode
            if (!canEdit) {
                addNotification("You do not have permission to edit this page.", "warning");
                return;
            }
            // Ensure editData is a fresh copy of the latest fetched data
            // Use functional update for safety if pageData might update async
            setEditData(currentEditData => JSON.parse(JSON.stringify(pageData || currentEditData)));
            updateIsEditing(true); // Update context state
            console.log("PageView: Entered edit mode.");
        }
    // Dependencies: Add functions called inside (handleSaveChanges) and state read (isEditing, canEdit, pageData)
    // Add context updaters (updateIsEditing) and other hooks (addNotification)
    }, [isEditing, canEdit, pageData, updateIsEditing, handleSaveChanges, addNotification]);


    const handleCancelEdit = useCallback(() => {
        console.log("PageView: Cancelling edit.");
        updateIsEditing(false); // Update context state
        setEditError(null); // Clear save errors
        // Reset editData back to the last successfully fetched canonical state
        if (pageData) {
            setEditData(JSON.parse(JSON.stringify(pageData)));
        } else {
             setEditData(null);
        }
    // Dependencies: pageData for reset, updateIsEditing to update context
    }, [pageData, updateIsEditing]);


    const handleCellChange = useCallback((rowIndex, colIndex, value) => {
         if (!isEditing) return;
        setEditData(prevData => {
            if (!prevData) return null;
             const newData = JSON.parse(JSON.stringify(prevData));
             if (newData.rows[rowIndex]?.cells) {
                 newData.rows[rowIndex].cells[colIndex] = value;
             } else {
                 console.warn(`Attempted to update non-existent cell in editData at [${rowIndex}, ${colIndex}]`);
             }
            return newData;
        });
    // Dependency: isEditing to gate the update
    }, [isEditing]);


     const handleAddRow = useCallback(() => {
         if (!isEditing || !editData) return;
         console.log("PageView: Adding new row to editData...");
         setEditData(prevData => {
             const newData = JSON.parse(JSON.stringify(prevData));
            const newOrder = newData.rows.length > 0 ? Math.max(0, ...newData.rows.map(r => r.order)) + 1 : 1;
            const newRow = {
                 id: null,
                 order: newOrder,
                 cells: Array(newData.columns.length).fill('')
            };
            newData.rows.push(newRow);
            return newData;
         });
     // Dependencies: isEditing and editData (to get columns length)
     }, [isEditing, editData]);


      const handleDeleteRow = useCallback((rowIdToDelete) => {
          if (!isEditing || !editData) return;
          console.log("PageView: Deleting row with ID:", rowIdToDelete);
          setEditData(prevData => {
              const newData = JSON.parse(JSON.stringify(prevData));
             newData.rows = newData.rows.filter(row => row.id !== rowIdToDelete);
             // Re-assign sequential 'order' based on the new array index
             newData.rows.forEach((row, index) => {
                 row.order = index + 1;
             });
             return newData;
          });
      // Dependencies: isEditing and editData (implicitly via setEditData)
      }, [isEditing, editData]); // editData is technically not needed if only using functional update

      // TODO: Implement handleAddColumn, handleDeleteColumn, handleColumnResize callbacks

      const handleDeletePageTrigger = useCallback(() => {
          if (!canEdit) {
             addNotification("You don't have permission to delete this page.", "warning");
             return;
          }
          setShowDeleteConfirm(true);
      // Dependencies: canEdit state, addNotification hook
      }, [canEdit, addNotification]);

      const confirmDeletePageAction = async () => {
          console.log("PageView: Confirming page delete...");
          setIsDeleting(true);
          try {
              await api.deletePage(pageSlug);
              if (!isMounted.current) return;
              addNotification(`Page "${pageData?.name || pageSlug}" deleted successfully.`, 'success');
              navigate('/pages', { replace: true }); // Navigate back to list
          } catch (err) {
              console.error("PageView: Failed to delete page:", err);
              if (!isMounted.current) return;
               const errorMsg = err.response?.data?.detail || "Could not delete page.";
              addNotification(errorMsg, 'error');
              // Don't navigate away on error
          } finally {
                if (isMounted.current) {
                    setIsDeleting(false);
                    setShowDeleteConfirm(false); // Close modal even on error? Yes.
                }
          }
      };

      const handleCreateTodoTrigger = useCallback(() => {
           if (!pageData) return; // Need page data first
           setShowCreateTodoModal(true);
       // Dependency: pageData to check if it's loaded
       }, [pageData]);


       // --- Register Actions with Context ---
       // This effect MUST run AFTER all the useCallback definitions it depends on.
       useEffect(() => {
         console.log("PageView: Registering actions with context.");
         // Pass the memoized callback functions to the context provider
         registerActions({
             toggleEdit: handleToggleEdit,
             addRow: handleAddRow,
             saveChanges: handleSaveChanges,
             cancelEdit: handleCancelEdit,
             triggerDeletePage: handleDeletePageTrigger,
             triggerCreateTodo: handleCreateTodoTrigger,
             // Pass other actions if/when implemented
         });
       }, [ // List ALL useCallback functions being registered as dependencies
           registerActions, handleToggleEdit, handleAddRow, handleSaveChanges,
           handleCancelEdit, handleDeletePageTrigger, handleCreateTodoTrigger
        ]);

        // --- Sync Context State ---
        // Keep the context's state in sync with this component's local state if needed
        // (Alternatively, context could be the single source of truth)
        useEffect(() => { updateIsEditing(isEditing); }, [isEditing, updateIsEditing]);
        useEffect(() => { updateIsLoadingSave(isLoadingSave); }, [isLoadingSave, updateIsLoadingSave]);
        // useEffect(() => { updateCanEdit(canEdit); }, [canEdit, updateCanEdit]); // Already updated in fetchData


    // --- Render Logic ---
    if (loading && !pageData) {
        return <div className="flex justify-center items-center h-[calc(100vh-120px)]"><LoadingSpinner size="lg" /></div>;
    }
    if (pageError && !pageData) {
        return <div className="p-4 md:p-6"><div className="p-4 text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300 border border-red-300 dark:border-red-700 rounded">{pageError}</div></div>;
    }
    if (!pageData) {
        return <div className="p-4 md:p-6">Page data could not be loaded.</div>;
    }

    // Use editData if editing, otherwise use the fetched pageData
    const displayData = (isEditing ? editData : pageData) || { columns: [], rows: [] };

    return (
        <div className="page-view flex flex-col h-full">
            {/* Editing Controls Bar */}
            {isEditing && (
                <div className="editing-controls bg-yellow-100 dark:bg-yellow-900/50 p-2 mb-3 rounded border border-yellow-400 dark:border-yellow-700 flex justify-end items-center gap-2 flex-shrink-0 shadow-sm">
                     <span className="text-yellow-800 dark:text-yellow-200 font-semibold mr-auto text-sm">Editing Mode</span>
                     {editError && <span className="text-red-600 dark:text-red-400 text-sm truncate max-w-xs" title={editError}>{editError}</span>}
                    <Button size="sm" variant="ghost" onClick={handleCancelEdit} disabled={isLoadingSave}>Cancel</Button>
                    <Button size="sm" variant="success" onClick={handleSaveChanges} isLoading={isLoadingSave} disabled={isLoadingSave} className="min-w-[90px]">Save Page</Button>
                </div>
            )}

            {/* Data Table */}
            <div className="flex-grow overflow-hidden">
                 {(displayData.columns && displayData.rows) ? (
                    <DataTable
                        columns={displayData.columns}
                        rows={displayData.rows}
                        isEditing={isEditing}
                        onCellChange={handleCellChange}
                        onDeleteRow={handleDeleteRow}
                        // Pass other handlers if implemented
                    />
                 ) : (
                    <div className="p-4 text-center text-gray-500">Table data is unavailable or invalid.</div>
                 )}
            </div>

            {/* Modals */}
            <ConfirmationModal
                isOpen={showDeleteConfirm}
                onClose={() => setShowDeleteConfirm(false)}
                onConfirm={confirmDeletePageAction}
                title="Confirm Page Deletion"
                message={`Are you sure you want to permanently delete the page "${pageData?.name || pageSlug}"? This action cannot be undone.`}
                confirmText="Delete Page"
                confirmVariant="danger"
                isLoading={isDeleting}
            />
             <CreateTodoModal
                 isOpen={showCreateTodoModal}
                 onClose={() => setShowCreateTodoModal(false)}
                 sourcePageSlug={pageSlug}
                 sourcePageName={pageData?.name || pageSlug}
             />
        </div>
    );
}

export default PageView;
