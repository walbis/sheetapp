import React from 'react';
import { Link } from 'react-router-dom';
import RegisterForm from '../components/auth/RegisterForm';

function RegisterPage() {
    return (
        // Center content vertically and horizontally
        <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 px-4">
            <div className="p-6 md:p-8 border border-table-border rounded-lg shadow-lg max-w-sm w-full bg-background">
                <h1 className="text-2xl font-bold text-primary mb-6 text-center">
                    Create Account
                </h1>
                {/* Render the registration form component */}
                <RegisterForm />
                 {/* Link back to Login page */}
                 <p className="text-center text-sm text-font-color mt-4">
                     Already have an account?{' '}
                     <Link to="/login" className="text-link-color hover:underline font-medium">
                         Login here
                     </Link>
                 </p>
            </div>
        </div>
    );
}

export default RegisterPage;