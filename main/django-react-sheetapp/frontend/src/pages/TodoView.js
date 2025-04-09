import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import DataTable from '../components/table/DataTable'; // Reusable DataTable
import LoadingSpinner from '../components/common/LoadingSpinner';
import * as api from '../services/api'; // API service functions
import { useNotification } from '../hooks/useNotification'; // Hook for notifications
import Button from '../components/common/Button'; // Button component
import ConfirmationModal from '../components/modals/ConfirmationModal'; // Confirmation modal

// Component to display a specific ToDo list derived from a page
function TodoView() {
    const { todoId } = useParams(); // Get ToDo ID (PK/UUID) from route parameter
    const navigate = useNavigate(); // Hook for navigation
    const { addNotification } = useNotification(); // Hook for displaying notifications

    // State for combined ToDo and source page data
    const [todoDisplayData, setTodoDisplayData] = useState(null); // { todoInfo, sourcePageInfo, rows }
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isDeleting, setIsDeleting] = useState(false); // Loading state for delete action
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false); // Delete modal visibility

    // Ref to track component mount status
    const isMounted = useRef(true);
    useEffect(() => {
        isMounted.current = true;
        return () => { isMounted.current = false; }; // Cleanup on unmount
    }, []);


    // --- Data Fetching ---
    const fetchTodoData = useCallback(async (abortController) => {
        if (!isMounted.current) return;
        setLoading(true);
        setError(null);
        console.log(`TodoView: Fetching data for ToDo ID: ${todoId}`);
        try {
            // 1. Fetch ToDo Detail (includes source page slug, name, creator, statuses)
            const todoResponse = await api.getTodoDetail(todoId, { signal: abortController?.signal });
            const fetchedTodo = todoResponse.data;
            if (!isMounted.current) return;

            // 2. Fetch Source Page Data (columns, rows with cell values) using slug from ToDo detail
            const pageResponse = await api.getPageData(fetchedTodo.source_page.slug, { signal: abortController?.signal });
            const sourcePage = pageResponse.data;
            if (!isMounted.current) return;

            // 3. Combine Data: Merge source page rows with ToDo statuses
            // Create a map for quick status lookup by row ID
            const statusMap = new Map(fetchedTodo.statuses.map(s => [s.row_id, s.status]));
            // Map through source page rows and add the corresponding status
            const combinedRows = sourcePage.rows.map(row => ({
                 ...row, // Includes row.id, row.order, row.cells array
                 status: statusMap.get(row.id) || 'NOT_STARTED', // Default if status missing
            }));

            // Prepare the final data structure for the view state
            const finalData = {
                todoInfo: fetchedTodo,          // Contains ToDo specific info (name, creator, etc.)
                sourcePageInfo: sourcePage,     // Contains columns structure and original cells
                rows: combinedRows,             // Rows combined with current status
            };

            setTodoDisplayData(finalData);
            console.log("TodoView: Data fetched and combined successfully:", finalData);

        } catch (err) {
             if (err.name === 'CanceledError') {
                 console.log("TodoView: Fetch aborted");
                 return;
             }
            console.error("TodoView: Failed to fetch data:", err.response?.data || err.message);
            if (!isMounted.current) return;

            const errorMsg = err.response?.data?.detail || err.response?.data?.error || "Could not load ToDo data.";
            setError(errorMsg);
            addNotification(errorMsg, 'error');
            if (err.response?.status === 404) setError("ToDo list or its source page not found.");
            if (err.response?.status === 403) setError("You do not have permission to view this ToDo list.");
        } finally {
            if (isMounted.current) setLoading(false);
        }
    }, [todoId, addNotification]); // Dependencies

    // Fetch data on initial load and when todoId changes
    useEffect(() => {
        const abortController = new AbortController();
        fetchTodoData(abortController);
        return () => {
             console.log("TodoView: Aborting fetch on unmount/ID change");
             abortController.abort();
         };
    }, [fetchTodoData]); // fetchData has todoId as dependency

     // --- Status Update Handler ---
      // useCallback ensures this function reference is stable unless dependencies change
      const handleStatusChange = useCallback(async (rowId, newStatus) => {
          if (!todoDisplayData) return; // Should not happen if data loaded

          console.log(`TodoView: Updating status for row ${rowId} to ${newStatus} in ToDo ${todoId}`);

          // --- Optimistic UI Update ---
          // Update local state immediately for better perceived performance.
          // Store the previous state in case we need to revert.
          const previousData = JSON.parse(JSON.stringify(todoDisplayData)); // Deep copy
          setTodoDisplayData(prevData => {
              if (!prevData) return null;
              const newRows = prevData.rows.map(row =>
                  row.id === rowId ? { ...row, status: newStatus } : row
              );
              return { ...prevData, rows: newRows };
          });
          // --- End Optimistic Update ---

          try {
              // Call the API to persist the status change
              await api.updateTodoStatus(todoId, rowId, newStatus);
              // No need to re-fetch on success if optimistic update was correct
              addNotification("Status updated!", "success", 2000); // Short success message
          } catch (err) {
              console.error("TodoView: Failed to update status:", err.response?.data || err.message);
               const errorMsg = err.response?.data?.detail || "Failed to update status.";
              addNotification(errorMsg, "error");
              // --- Revert Optimistic Update on Error ---
              if (isMounted.current) {
                  setTodoDisplayData(previousData); // Restore previous state
              }
              // Optionally re-fetch to ensure consistency: await fetchTodoData();
          }
      }, [todoId, todoDisplayData, addNotification]); // Dependencies for the handler


      // --- Delete ToDo Handler ---
      const triggerDeleteTodo = () => {
         // TODO: Add permission check if needed (e.g., only creator/admin can delete)
         // Currently relies on backend permission check for the API call itself.
         setShowDeleteConfirm(true);
      };

      const confirmDeleteTodoAction = async () => {
         console.log("TodoView: Confirming ToDo delete...");
         setIsDeleting(true);
         try {
             await api.deleteTodo(todoId);
             if (!isMounted.current) return;
             addNotification(`ToDo list "${todoDisplayData?.todoInfo?.name || todoId}" deleted.`, 'success');
             navigate('/todos', { replace: true }); // Navigate back to ToDo list
         } catch (err) {
             console.error("TodoView: Failed to delete ToDo:", err);
              if (!isMounted.current) return;
              const errorMsg = err.response?.data?.detail || "Could not delete ToDo list.";
             addNotification(errorMsg, 'error');
             setIsDeleting(false);
             setShowDeleteConfirm(false);
         }
          // No finally block needed as we navigate away on success
      };


    // --- Render Logic ---
    if (loading) {
        return <div className="flex justify-center items-center h-[calc(100vh-120px)]"><LoadingSpinner size="lg" /></div>;
    }

    if (error) {
        return <div className="p-4 md:p-6 text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300 border border-red-300 dark:border-red-700 rounded">{error}</div>;
    }

    if (!todoDisplayData) {
        return <div className="p-4 md:p-6">ToDo list data could not be loaded.</div>;
    }

    const { todoInfo, sourcePageInfo, rows } = todoDisplayData;

    return (
        <div className="todo-view p-4 md:p-6 flex flex-col h-full">
            {/* Header Information */}
            <div className="mb-4 flex-shrink-0">
                 <div className="flex flex-wrap justify-between items-center gap-2 mb-2">
                     <h1 className="text-xl md:text-2xl font-bold text-primary inline-block mr-3 break-all">
                         ToDo: {todoInfo.name}
                     </h1>
                     <div className="flex items-center gap-2">
                          {todoInfo.is_personal && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full dark:bg-blue-900 dark:text-blue-200 flex-shrink-0">
                                  Personal
                              </span>
                          )}
                         {/* TODO: Add permission check before showing delete button */}
                         <Button variant="danger" size="sm" onClick={triggerDeleteTodo}>
                             Delete ToDo
                         </Button>
                     </div>
                 </div>
                 <p className="text-sm text-font-color opacity-80 mb-1">
                     Based on page: <Link to={`/pages/${sourcePageInfo.slug}`} className="text-link-color hover:underline font-medium">{sourcePageInfo.name}</Link>
                 </p>
                 <p className="text-sm text-font-color opacity-80 mb-1">
                     Created by: {todoInfo.creator?.email || 'N/A'} on {new Date(todoInfo.created_at).toLocaleDateString()}
                 </p>
            </div>

            {/* Data Table for ToDo */}
            <div className="flex-grow overflow-hidden"> {/* Container allows DataTable to scroll */}
                <DataTable
                    // Pass columns from the source page
                    columns={sourcePageInfo.columns}
                    // Pass rows combined with status information
                    rows={rows}
                    isEditing={false} // ToDo view is generally read-only for structure/cells
                    isTodoTable={true} // IMPORTANT: Enable the status column feature
                    onStatusChange={handleStatusChange} // Pass the status update handler
                />
            </div>
             <p className="text-xs italic text-gray-500 mt-2 flex-shrink-0">
                 Status changes are saved automatically. Cell content reflects the source page and is read-only here.
             </p>

             {/* Delete Confirmation Modal */}
             <ConfirmationModal
                 isOpen={showDeleteConfirm}
                 onClose={() => setShowDeleteConfirm(false)}
                 onConfirm={confirmDeleteTodoAction}
                 title="Delete ToDo List"
                 message={`Are you sure you want to delete the ToDo list "${todoInfo.name}"? This cannot be undone.`}
                 confirmText="Delete ToDo"
                 confirmVariant="danger"
                 isLoading={isDeleting}
             />
        </div>
    );
}

export default TodoView;