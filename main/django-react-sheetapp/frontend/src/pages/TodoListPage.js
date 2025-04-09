import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import * as api from '../services/api'; // API service functions
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useNotification } from '../hooks/useNotification'; // Hook for notifications
import Button from '../components/common/Button'; // If actions like delete are added

// Page component to display a list of user-accessible ToDo lists
function TodoListPage() {
    const [todos, setTodos] = useState([]); // State for the list of ToDo lists
    const [loading, setLoading] = useState(true); // Loading state
    const [error, setError] = useState(null); // Error state
    const { addNotification } = useNotification(); // Notification hook

    // Function to fetch ToDo lists from the API
    const fetchTodos = useCallback(async () => {
        setLoading(true);
        setError(null);
        console.log("TodoList: Fetching ToDo lists...");
        try {
            const response = await api.getTodos();
            // Handle potential pagination or direct array
            const todoList = response.data?.results || response.data || [];
            setTodos(todoList);
            console.log(`TodoList: Fetched ${todoList.length} ToDo lists.`);
        } catch (err) {
            console.error("TodoList: Failed to fetch ToDo lists:", err.response?.data || err.message);
            const errorMsg = err.response?.data?.detail || "Could not load your ToDo lists.";
            setError(errorMsg);
            // Show notification for critical errors like unauthorized access
            if (err.response?.status === 401 || err.response?.status === 403) {
                addNotification("Could not load ToDo lists. Please log in again.", 'error');
            } else {
                // Optionally notify for other errors, or just display message
                // addNotification(errorMsg, 'error');
            }
        } finally {
            setLoading(false);
        }
    }, [addNotification]); // Dependency: addNotification (stable ref)

    // Fetch ToDo lists when the component mounts
    useEffect(() => {
        fetchTodos();
    }, [fetchTodos]); // fetchTodos is memoized, runs once on mount

    // --- Render Logic ---

    return (
         <div className="p-4 md:p-6">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-primary">My ToDo Lists</h1>
                {/* Add filter/sort options here later if needed */}
            </div>

            {/* Loading State */}
            {loading && (
                <div className="flex justify-center items-center py-10">
                    <LoadingSpinner size="lg" />
                </div>
            )}

            {/* Error State */}
             {error && !loading && (
                 <div className="p-4 text-center text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300 border border-red-300 dark:border-red-700 rounded shadow-sm">
                     {error}
                 </div>
             )}

             {/* Empty State */}
             {!loading && !error && todos.length === 0 && (
                 <div className="p-6 text-center text-gray-500 dark:text-gray-400 bg-background border border-dashed border-table-border rounded italic">
                     You don't have any ToDo lists yet. Go to a Page and click the "ToDo" button to create one.
                 </div>
             )}

             {/* ToDo List Items */}
             {!loading && !error && todos.length > 0 && (
                 <div className="space-y-3"> {/* Vertical spacing between cards */}
                     {todos.map(todo => (
                         <Link
                             key={todo.id}
                             // Use todo.id (UUID primary key) for the route parameter
                             to={`/todos/${todo.id}`}
                             className="block p-4 bg-background border border-table-border rounded shadow-sm hover:shadow-md hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background transition-all duration-150 ease-in-out"
                         >
                             {/* ToDo Card Header */}
                             <div className="flex justify-between items-start mb-1">
                                 {/* ToDo Name */}
                                 <h2 className="text-base md:text-lg font-semibold text-link-color truncate pr-2" title={todo.name}>
                                     {todo.name}
                                 </h2>
                                 {/* Personal Badge (if applicable) */}
                                 {todo.is_personal && (
                                     <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full dark:bg-blue-900 dark:text-blue-200 flex-shrink-0">
                                         Personal
                                     </span>
                                 )}
                             </div>
                             {/* Source Page Link */}
                             <p className="text-xs text-font-color opacity-70 mb-1">
                                 From Page:
                                 <span className="font-medium ml-1 underline hover:text-primary">
                                     {/* Link to the source page */}
                                      <Link to={`/pages/${todo.source_page_slug}`} onClick={(e) => e.stopPropagation()} className="hover:underline">
                                         {todo.source_page_name || todo.source_page_slug}
                                     </Link>
                                 </span>
                             </p>
                             {/* Creator and Date */}
                             <p className="text-xs text-font-color opacity-70">
                                 Created by: {todo.creator?.email || 'N/A'} on {new Date(todo.created_at).toLocaleDateString()}
                             </p>
                         </Link>
                     ))}
                 </div>
             )}
        </div>
    );
}

export default TodoListPage;