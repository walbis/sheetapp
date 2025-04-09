import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Topbar from './Topbar';
import Sidebar from './Sidebar';
import { PageActionProvider } from '../../contexts/PageActionContext'; // Import context provider

function MainLayout() {
    // Manage sidebar state, persist preference in localStorage
    const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
         try {
             const savedState = localStorage.getItem('sidebarOpen');
             // Default to true (open) if no saved state or if parsing fails
             return savedState !== null ? JSON.parse(savedState) : true;
         } catch (error) {
             console.error("Error reading sidebar state from localStorage", error);
             return true; // Default to open on error
         }
    });

    const location = useLocation(); // Hook to get current route information

    // Effect to save sidebar state whenever it changes
    useEffect(() => {
         try {
            localStorage.setItem('sidebarOpen', JSON.stringify(isSidebarOpen));
         } catch (error) {
             console.error("Error saving sidebar state to localStorage", error);
         }
    }, [isSidebarOpen]);

    // Function to toggle sidebar state
    const toggleSidebar = () => {
        setIsSidebarOpen(prev => !prev);
    };

     // Determine if the current route is a specific page view (e.g., /pages/some-slug)
     // This helps decide whether to wrap the content with the PageActionProvider.
     const isPageView = location.pathname.startsWith('/pages/') && location.pathname.split('/').length > 2 && location.pathname.split('/')[2] !== '';
     // Add similar logic for ToDo view if it needs context
     // const isTodoView = location.pathname.startsWith('/todos/') && location.pathname.split('/').length > 2;

     // Component to render the main content area where child routes appear
     const MainContentOutlet = () => (
        <main className="main-content overflow-y-auto p-4 md:p-6 bg-background">
             {/* Outlet renders the matched child route component (e.g., PageView, PageList) */}
            <Outlet />
        </main>
    );

    // Define the grid layout class dynamically based on sidebar state
    const gridLayoutClass = `grid h-[calc(100vh-60px)] overflow-hidden ${isSidebarOpen ? 'grid-cols-[200px_1fr]' : 'grid-cols-[0px_1fr]'} transition-[grid-template-columns] duration-300 ease-in-out`;

    return (
        // The root element for this layout, assuming #root in index.css sets up the top-level rows
        <>
            {/* Render Topbar - Pass toggle function and current state */}
            {/* Conditionally provide PageAction context based on route */}
            {isPageView ? (
                 <PageActionProvider> {/* Wrap only PageView related components */}
                     <Topbar toggleSidebar={toggleSidebar} isSidebarOpen={isSidebarOpen} />
                     <div className={gridLayoutClass}>
                         <Sidebar isOpen={isSidebarOpen} />
                         <MainContentOutlet />
                     </div>
                 </PageActionProvider>
            ) : ( // Render without PageAction context for other views
                 <>
                     <Topbar toggleSidebar={toggleSidebar} isSidebarOpen={isSidebarOpen} />
                     <div className={gridLayoutClass}>
                         <Sidebar isOpen={isSidebarOpen} />
                         <MainContentOutlet />
                     </div>
                 </>
            )}
        </>
    );
}

export default MainLayout;