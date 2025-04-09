import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../hooks/useAuth'; // To check if logged in
import * as api from '../../services/api'; // Import API functions
import LoadingSpinner from '../common/LoadingSpinner';
import CreatePageModal from '../modals/CreatePageModal';
import { useNotification } from '../../hooks/useNotification';

function Sidebar({ isOpen }) {
    const { theme, toggleTheme, partyModeActive, togglePartyMode } = useTheme();
    const { isAuthenticated } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const { addNotification } = useNotification();

    const [pages, setPages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    // Function to fetch the list of pages accessible by the user
    const fetchPages = async () => {
        if (!isAuthenticated) {
            setPages([]); // Clear pages if user logs out
            setError(null); // Clear error on logout
            return;
        }
        setLoading(true);
        setError(null);
        console.log("Sidebar: Fetching pages list...");
        try {
            const response = await api.getPages();
            // Handle potential pagination structure or direct array
            const pageList = response.data?.results || response.data || [];
            setPages(pageList);
            console.log(`Sidebar: Fetched ${pageList.length} pages.`);
        } catch (err) {
            console.error("Sidebar: Failed to fetch pages:", err.response?.data || err.message);
            const errorMsg = err.response?.data?.detail || "Could not load pages list.";
            setError(errorMsg);
            // Avoid showing notification for routine list fetch errors unless critical (like 401)
            if (err.response?.status === 401 || err.response?.status === 403) {
                 addNotification("Session expired or invalid. Please log in again.", "error");
                 // Optionally trigger logout context action here
            }
        } finally {
            setLoading(false);
        }
    };

    // Fetch pages when authentication status changes, or on initial mount if authenticated
    useEffect(() => {
        fetchPages();
        // Re-fetch whenever authentication status changes
    }, [isAuthenticated]); // Dependency on auth status ensures re-fetch on login/logout

    // Function called after a page is successfully created via the modal
     const handlePageCreated = (newPage) => {
        setIsCreateModalOpen(false); // Close the modal
        addNotification(`Page "${newPage.name}" created successfully!`, 'success');
        // Option 1: Refetch the entire list (simpler, ensures consistency)
        // fetchPages();
        // Option 2: Optimistically add to the list and navigate
        setPages(prev => [newPage, ...prev.filter(p => p.slug !== newPage.slug)]); // Add to start, prevent duplicates
        navigate(`/pages/${newPage.slug}`); // Navigate to the new page
    };

    // Render nothing if the sidebar is explicitly closed via props
    if (!isOpen) {
        // Optionally return a slim version or an icon bar for collapsed state
        return null;
    }

    return (
        // Apply transition for smooth opening/closing (handled by parent grid change)
        <aside className="sidebar border-r border-table-border p-3 flex flex-col h-full bg-background text-font-color overflow-y-auto">
            {/* Header */}
            <div className="header flex justify-between items-center mb-4 flex-shrink-0">
                {/* Title */}
                <h2 id="menu-title" className="text-base font-bold text-primary uppercase tracking-wider">
                    Pages
                </h2>
                {/* Control Buttons */}
                <div className="sidebar-buttons flex gap-1.5 items-center">
                     <button
                        id="party-mode"
                        onClick={togglePartyMode}
                        title="Toggle Party Mode"
                        aria-pressed={partyModeActive}
                        className={`flex items-center justify-center w-7 h-7 border border-table-border rounded-full cursor-pointer text-base transition-all duration-300 hover:scale-110 focus:outline-none focus:ring-1 focus:ring-primary ${partyModeActive ? 'bg-primary text-background' : 'bg-background text-font-color'}`}
                    >
                        😎
                    </button>
                    <button
                        id="theme-toggle"
                        onClick={toggleTheme}
                        title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
                        aria-label="Toggle theme"
                        className="flex items-center justify-center w-7 h-7 border border-table-border rounded-full cursor-pointer text-base transition-transform duration-300 hover:scale-110 focus:outline-none focus:ring-1 focus:ring-primary bg-background text-font-color"
                    >
                        {theme === 'dark' ? '🌙' : '🌞'}
                    </button>
                    <button
                         id="add-page"
                         title="Create New Page"
                         aria-label="Create New Page"
                         onClick={() => setIsCreateModalOpen(true)}
                         className="w-7 h-7 border border-table-border rounded-full bg-background text-font-color cursor-pointer text-xl font-bold flex items-center justify-center hover:bg-hover-bg hover:text-primary transition-all duration-300 focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                        +
                    </button>
                </div>
            </div>

            {/* Page List Area */}
            <ul id="page-list" className="list-none p-0 m-0 border-t border-table-border flex-grow overflow-y-auto min-h-0"> {/* Allow shrinking and scrolling */}
                 {/* Loading State */}
                 {loading && (
                     <li className="p-4 text-center flex justify-center items-center">
                         <LoadingSpinner size="md" />
                     </li>
                 )}
                 {/* Error State */}
                 {error && !loading && (
                     <li className="p-3 text-red-500 bg-red-100 dark:bg-red-900 dark:text-red-300 border border-red-300 dark:border-red-700 rounded text-sm">
                         {error}
                     </li>
                 )}
                 {/* Empty State */}
                 {!loading && !error && pages.length === 0 && (
                     <li className="p-3 text-sm text-gray-500 dark:text-gray-400 italic">
                         No pages found. Create one!
                     </li>
                 )}
                 {/* Page List Items */}
                 {!loading && !error && pages.map((page) => (
                    <li key={page.id || page.slug} className="border-b border-table-border">
                        <Link
                            to={`/pages/${page.slug}`}
                            // Dynamically set active class based on current location
                            className={`block p-2 text-sm hover:bg-hover-bg truncate transition-colors duration-150 focus:outline-none focus:ring-1 focus:ring-inset focus:ring-primary ${location.pathname === `/pages/${page.slug}` ? 'bg-hover-bg text-primary font-semibold' : 'text-font-color'}`}
                            title={page.name} // Tooltip for truncated names
                        >
                            {page.name}
                        </Link>
                    </li>
                ))}
            </ul>

            {/* Render Create Page Modal (controlled by state) */}
            <CreatePageModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onPageCreated={handlePageCreated} // Pass callback to refresh list/navigate
             />
        </aside>
    );
}

export default Sidebar;