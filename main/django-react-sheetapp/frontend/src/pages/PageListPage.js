import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Use useNavigate for navigation
import * as api from '../services/api'; // API service functions
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button'; // Reusable Button
import CreatePageModal from '../components/modals/CreatePageModal'; // Modal for creation
import { useNotification } from '../hooks/useNotification'; // Hook for notifications

// Page component to display a list of user-accessible pages
function PageListPage() {
    const [pages, setPages] = useState([]); // State for the list of pages
    const [loading, setLoading] = useState(true); // State for loading indicator
    const [error, setError] = useState(null); // State for storing fetch errors
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false); // State for modal visibility
    const { addNotification } = useNotification(); // Get notification function
    const navigate = useNavigate(); // Hook for programmatic navigation

    // Function to fetch pages from the API
    const fetchPages = useCallback(async () => {
        setLoading(true);
        setError(null);
        console.log("PageList: Fetching pages...");
        try {
            const response = await api.getPages();
            // Handle potential pagination structure (response.data.results) or direct array
            const pageList = response.data?.results || response.data || [];
            setPages(pageList);
            console.log(`PageList: Fetched ${pageList.length} pages.`);
        } catch (err) {
            console.error("PageList: Failed to fetch pages:", err.response?.data || err.message);
            const errorMsg = err.response?.data?.detail || "Could not load your pages.";
            setError(errorMsg);
            // Show error notification only for significant errors (like auth failure)
            if (err.response?.status === 401 || err.response?.status === 403) {
                 addNotification("Could not load pages. Please log in again.", 'error');
            } else {
                 // Don't show notification for general fetch errors on list view? Optional.
                 // addNotification(errorMsg, 'error');
            }
        } finally {
            setLoading(false);
        }
    }, [addNotification]); // Dependency: addNotification (stable ref usually)

    // Fetch pages when the component mounts
    useEffect(() => {
        fetchPages();
    }, [fetchPages]); // Run fetchPages on mount and if fetchPages reference changes (it shouldn't)

    // Callback function passed to CreatePageModal.
    // Called after a page is successfully created.
    const handlePageCreated = (newPage) => {
         setIsCreateModalOpen(false); // Close the modal
         addNotification(`Page "${newPage.name}" created successfully!`, 'success');
         // Navigate to the newly created page immediately
         navigate(`/pages/${newPage.slug}`);
         // Note: We don't need to manually add to the 'pages' state here because
         // navigating to the new page will cause this list component to unmount,
         // and it will refetch when the user navigates back.
         // If we wanted to stay on the list page, we'd use:
         // setPages(prev => [newPage, ...prev.filter(p => p.slug !== newPage.slug)]);
     };


    // --- Render Logic ---

    return (
        <div className="p-4 md:p-6">
            {/* Header Section */}
            <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
                <h1 className="text-2xl font-bold text-primary">My Pages</h1>
                {/* Button to open the Create Page modal */}
                 <Button
                    variant="primary"
                    onClick={() => setIsCreateModalOpen(true)}
                    aria-label="Create New Page"
                 >
                     + Create New Page
                 </Button>
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
             {!loading && !error && pages.length === 0 && (
                 <div className="p-6 text-center text-gray-500 dark:text-gray-400 bg-background border border-dashed border-table-border rounded italic">
                     You haven't created any pages yet. Click "+ Create New Page" to start!
                 </div>
             )}

             {/* Page List Grid */}
             {!loading && !error && pages.length > 0 && (
                 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                     {pages.map(page => (
                         <Link
                             key={page.id || page.slug} // Use unique key
                             to={`/pages/${page.slug}`} // Link to the specific page view
                             className="block p-4 bg-background border border-table-border rounded shadow-sm hover:shadow-md hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background transition-all duration-150 ease-in-out"
                         >
                             {/* Page Name (truncated) */}
                             <h2 className="text-base font-semibold text-link-color truncate mb-1" title={page.name}>
                                 {page.name}
                             </h2>
                             {/* Page Owner */}
                             <p className="text-xs text-font-color opacity-70 mb-1 truncate" title={page.owner?.email || 'N/A'}>
                                 Owner: {page.owner?.email || 'N/A'}
                             </p>
                             {/* Last Updated Timestamp */}
                             <p className="text-xs text-font-color opacity-70">
                                 Updated: {new Date(page.updated_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                             </p>
                         </Link>
                     ))}
                 </div>
             )}

              {/* Render the Create Page Modal (controlled by state) */}
              <CreatePageModal
                  isOpen={isCreateModalOpen}
                  onClose={() => setIsCreateModalOpen(false)}
                  onPageCreated={handlePageCreated} // Pass the callback
              />
        </div>
    );
}

export default PageListPage;