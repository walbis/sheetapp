import React from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { usePageActions } from '../../hooks/usePageActions'; // Import page actions hook
import Button from '../common/Button'; // Use reusable button component
import LoadingSpinner from '../common/LoadingSpinner'; // Import spinner

function Topbar({ toggleSidebar, isSidebarOpen }) {
    const location = useLocation();
    const { pageSlug } = useParams(); // Get pageSlug from URL parameters
    const { user, logout } = useAuth(); // Get user info and logout function

    // Attempt to get page actions context. It will be null if not on a PageView.
    const pageActionContext = usePageActions(); // Returns context value or default object

    // Safely destructure with defaults, checking if context exists
    const {
        isEditing = false,
        canEdit = false,      // Does the current user have edit rights for this page?
        isLoadingSave = false, // Is a save operation in progress?
        toggleEdit = () => {}, // Function to toggle edit mode / trigger save
        addRow = () => {},     // Function to add a row (only available when editing)
        triggerDeletePage = () => {}, // Function to initiate page deletion (shows confirmation)
        triggerCreateTodo = () => {}, // Function to open the create ToDo modal
     } = pageActionContext || {}; // Use defaults if context is null

    // Determine if page-specific action buttons should be shown:
    // 1. Must be on a specific page route (has pageSlug)
    // 2. Must have the PageActionContext available (meaning PageView provided it)
    const showPageActions = !!(location.pathname.startsWith('/pages/') && pageSlug && pageActionContext.registerActions); // Check if registerActions exists as proxy for context presence

    // Function to determine the title displayed in the Topbar
    const getPageTitle = () => {
        // Improve this by fetching actual page/todo names if context provides them
        if (pageSlug && location.pathname.includes('/pages/')) {
            // Could potentially get page name from pageData via context if needed
            return `Page: ${pageSlug}`;
        }
        // Add logic for ToDo title when ToDo view is implemented
        // if (todoId && location.pathname.includes('/todos/')) return `ToDo: ${todoId}`;
        if (location.pathname === '/pages') return 'My Pages';
        if (location.pathname === '/todos') return 'My ToDos';
        if (location.pathname === '/mainmenu') return 'Main Menu';
        return 'Sheet App'; // Default application title
    };

    // Handle user logout action
    const handleLogout = async () => {
         await logout();
         // Navigation should be handled automatically by PrivateRoute detecting auth change
         // Fallback redirect if needed:
         // window.location.href = '/login';
    }

    return (
        // Header element styling
        <header className="topbar flex items-center justify-between border-b border-table-border px-3 h-[60px] bg-background text-font-color flex-shrink-0 shadow-sm">

            {/* Left Section: Menu Toggle, Navigation Links, Page Title */}
            <div className="flex items-center gap-2 md:gap-3 overflow-hidden"> {/* Prevent stretching */}
                {/* Sidebar Toggle Button */}
                <button
                    id="menu-button"
                    onClick={toggleSidebar}
                    className="bg-transparent border-none text-2xl cursor-pointer p-1 hover:text-primary focus:outline-none focus:ring-1 focus:ring-primary rounded flex-shrink-0"
                    aria-label={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                    aria-expanded={isSidebarOpen}
                >
                    ☰
                </button>

                {/* Top Menu Navigation Links (Hidden on smaller screens) */}
                <nav className="hidden md:flex items-center gap-3 lg:gap-4 ml-1">
                    {/* Use NavLink for active styling later if desired */}
                    <Link to="/mainmenu" className={`top-menu-item px-3 py-1 rounded text-sm font-medium transition-colors ${location.pathname === '/mainmenu' ? 'text-primary bg-hover-bg' : 'text-font-color hover:bg-hover-bg'}`}>Main Menu</Link>
                    <Link to="/pages" className={`top-menu-item px-3 py-1 rounded text-sm font-medium transition-colors ${location.pathname.startsWith('/pages') ? 'text-primary bg-hover-bg' : 'text-font-color hover:bg-hover-bg'}`}>Pages</Link>
                    <Link to="/todos" className={`top-menu-item px-3 py-1 rounded text-sm font-medium transition-colors ${location.pathname.startsWith('/todos') ? 'text-primary bg-hover-bg' : 'text-font-color hover:bg-hover-bg'}`}>ToDo</Link>
                </nav>

                 {/* Dynamic Page Title (Hidden on smaller screens) */}
                 <h1 className="text-base lg:text-lg font-semibold ml-2 md:ml-4 text-primary truncate hidden md:block flex-shrink min-w-0 pr-2" title={getPageTitle()}>
                     {getPageTitle()}
                 </h1>
            </div>

            {/* Right Section: Action Buttons, User Info */}
            <div className="flex items-center gap-2 md:gap-3">
                 {/* Conditional Page Action Buttons - Show only on specific page view and if user can edit */}
                {showPageActions && canEdit && (
                     <div className="actions flex gap-1.5 md:gap-2 items-center">
                        {/* Add Row Button - Enabled only when editing */}
                        <Button size="sm" variant="success" onClick={addRow} disabled={!isEditing || isLoadingSave} title={!isEditing ? "Enter edit mode to add row" : "Add Row"}>
                             Add Row
                        </Button>
                        {/* Create ToDo Button - Always enabled if user can edit page */}
                        <Button size="sm" variant="warning" onClick={triggerCreateTodo} disabled={isLoadingSave} title="Create ToDo list from this page">
                             ToDo
                        </Button>
                        {/* Edit/Save Button */}
                        <Button
                            size="sm"
                            variant={isEditing ? 'primary' : 'ghost'} // Primary when editing (Save), Ghost when not (Edit)
                            onClick={toggleEdit} // Calls toggleEdit or handleSaveChanges via context
                            disabled={isLoadingSave} // Disable while saving is in progress
                            isLoading={isEditing && isLoadingSave} // Show spinner only when saving
                            className="min-w-[60px]" // Ensure minimum width
                            title={isEditing ? "Save changes" : "Enter edit mode"}
                        >
                            {isEditing ? 'Save' : 'Edit'}
                        </Button>
                        {/* Delete Page Button */}
                         <Button size="sm" variant="danger" onClick={triggerDeletePage} disabled={isLoadingSave} title="Delete this page">
                             Delete Page
                         </Button>
                    </div>
                )}
                 {/* Indication for View-Only Mode */}
                  {showPageActions && !canEdit && (
                     <span className="text-xs md:text-sm text-gray-500 dark:text-gray-400 italic mr-2 border border-table-border px-2 py-1 rounded-full">View Mode</span>
                 )}


                {/* User Information and Logout Button */}
                {user && (
                    <div className="flex items-center gap-2 border-l border-table-border pl-2 md:pl-3 ml-1 md:ml-2">
                        {/* Display user email (truncated on small screens) */}
                        <span className="text-xs md:text-sm hidden sm:inline truncate max-w-[100px] md:max-w-[150px]" title={user.email}>
                            {user.email}
                        </span>
                        {/* Logout Button */}
                        <Button size="sm" variant="secondary" onClick={handleLogout} title="Logout">
                            Logout
                        </Button>
                    </div>
                )}
            </div>
        </header>
    );
}

export default Topbar;