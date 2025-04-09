import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate, useLocation, Link } from 'react-router-dom'; // Import Link
import LoadingSpinner from '../common/LoadingSpinner';
import Button from '../common/Button'; // Use Button component

function LoginForm() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    // Determine where to redirect after login - default to /pages
    const from = location.state?.from?.pathname || "/pages";

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(''); // Clear previous errors
        setLoading(true);
        try {
            const result = await login(email, password);
            if (result.success) {
                console.log("Login successful, navigating to:", from);
                navigate(from, { replace: true }); // Redirect to intended page or default
            } else {
                // Use the error message provided by the login function
                setError(result.error || 'Login failed. Please check your credentials.');
            }
        } catch (err) {
            // Catch unexpected errors during the login process itself
            console.error("Login component catch:", err);
            setError('An unexpected error occurred during login.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {/* Display general error messages */}
            {error && (
                 <p className="text-red-500 dark:text-red-400 text-sm bg-red-100 dark:bg-red-900 p-2 rounded border border-red-300 dark:border-red-700">
                     {error}
                 </p>
            )}
            <div>
                <label htmlFor="login-email" className="block text-sm font-medium text-font-color mb-1">Email Address</label>
                <input
                    type="email"
                    id="login-email" // Unique ID
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    className="w-full p-2 border border-table-border rounded bg-background text-font-color focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50 dark:placeholder-gray-500"
                    placeholder="you@example.com"
                    disabled={loading}
                />
            </div>
            <div>
                <label htmlFor="login-password" className="block text-sm font-medium text-font-color mb-1">Password</label>
                <input
                    type="password"
                    id="login-password" // Unique ID
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="w-full p-2 border border-table-border rounded bg-background text-font-color focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                    placeholder="••••••••"
                    disabled={loading}
                />
            </div>
            <Button
                type="submit"
                variant="primary"
                disabled={loading}
                className="w-full" // Make button full width
            >
                {loading ? <LoadingSpinner size="sm" color="text-white" /> : 'Login'}
            </Button>
            {/* Link to Register Page */}
             <p className="text-center text-sm text-font-color mt-4">
                 Don't have an account?{' '}
                 <Link to="/register" className="text-link-color hover:underline font-medium">
                     Register here
                 </Link>
             </p>
        </form>
    );
}

export default LoginForm;