import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage'; // Placeholder for /mainmenu
import PageListPage from './pages/PageListPage';   // For /pages list
import TodoListPage from './pages/TodoListPage';   // For /todos list
import PageView from './pages/PageView';         // For /pages/:pageSlug
import TodoView from './pages/TodoView';         // For /todos/:todoId
import { useAuth } from './hooks/useAuth'; // Hook to check authentication state
import LoadingSpinner from './components/common/LoadingSpinner'; // Loading indicator
import NotificationDisplay from './components/common/NotificationDisplay'; // Global notifications

// Component to protect routes, requires user to be authenticated
function PrivateRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth(); // Get auth state from context
  const location = useLocation(); // Get current location to redirect back after login

  // Show loading spinner while authentication status is being checked
  if (isLoading) {
    return (
        <div className="flex justify-center items-center h-screen bg-background">
            <LoadingSpinner size="lg" />
        </div>
    );
  }

  // If user is not authenticated, redirect them to the login page
  // Preserve the location they were trying to access using 'state'
  if (!isAuthenticated) {
     console.log("PrivateRoute: Not authenticated, redirecting to login from:", location.pathname);
     return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If authenticated, render the child components (the protected route)
  return children;
}

// Main Application Component
function App() {
   const { isLoading: isAuthLoading } = useAuth(); // Optionally use loading state globally

   // Example effect to run after auth state is determined
   useEffect(() => {
      if (!isAuthLoading) {
         // console.log("App: Auth state initialized.");
      }
   }, [isAuthLoading]);

  return (
     <>
         {/* Global Notification Display Area */}
         <NotificationDisplay />

         {/* Define Application Routes */}
         <Routes>
             {/* --- Public Routes --- */}
             <Route path="/login" element={<LoginPage />} />
             <Route path="/register" element={<RegisterPage />} />

             {/* --- Protected Routes --- */}
             {/* All routes under "/*" require authentication via PrivateRoute */}
             {/* These routes also use the MainLayout (Topbar, Sidebar) */}
             <Route
                 path="/*" // Match all potential protected paths
                 element={
                     <PrivateRoute>
                         <MainLayout />
                     </PrivateRoute>
                 }
             >
                 {/* Default route inside protected area (e.g., redirect to pages list) */}
                 <Route index element={<Navigate to="/pages" replace />} />

                 {/* Specific protected routes */}
                 <Route path="mainmenu" element={<DashboardPage />} />
                 <Route path="pages" element={<PageListPage />} />
                 <Route path="todos" element={<TodoListPage />} />
                 <Route path="pages/:pageSlug" element={<PageView />} />
                 {/* Route for viewing a specific ToDo list using its ID */}
                 <Route path="todos/:todoId" element={<TodoView />} />

                 {/* Add other nested protected routes here (e.g., /settings, /profile) */}
                 {/* <Route path="settings" element={<SettingsPage />} /> */}

                 {/* Fallback/Catch-all for any undefined paths inside the protected area */}
                 {/* Redirects to the default protected route (/pages) */}
                 <Route path="*" element={<Navigate to="/pages" replace />} />
             </Route>

             {/* Optional: A global fallback for completely unmatched routes (if not handled above) */}
             {/* <Route path="*" element={<NotFoundPage />} /> */}

         </Routes>
     </>
  );
}

export default App;