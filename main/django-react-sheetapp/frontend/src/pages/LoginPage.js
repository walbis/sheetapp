import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth'; // Use auth hook to check loading state
import LoadingSpinner from '../components/common/LoadingSpinner';

function LoginPage() {
     // Get auth loading state to potentially show a message while checking session
     const { isLoading } = useAuth();
     const location = useLocation();

     // Check if there's a message passed via state (e.g., after logout or session expiry)
     const message = location.state?.message;

    return (
        // Center content vertically and horizontally
        <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 px-4">
            <div className="p-6 md:p-8 border border-table-border rounded-lg shadow-lg max-w-sm w-full bg-background">
                <h1 className="text-2xl font-bold text-primary mb-6 text-center">
                    Sheet App Login
                </h1>

                {/* Display message if passed */}
                {message && (
                     <p className="text-center text-sm text-green-600 dark:text-green-400 mb-4">{message}</p>
                 )}

                 {/* Show spinner only if initial auth check is still loading */}
                 {isLoading ? (
                     <div className="flex flex-col justify-center items-center p-4 min-h-[150px]">
                         <LoadingSpinner size="lg" />
                         <p className="mt-3 text-sm text-font-color opacity-80">Checking session...</p>
                     </div>
                 ) : (
                     // Show login form when not loading
                     <LoginForm />
                 )}
            </div>
        </div>
    );
}

export default LoginPage;