import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate, Link } from 'react-router-dom'; // Import Link
import LoadingSpinner from '../common/LoadingSpinner';
import { useNotification } from '../../hooks/useNotification';
import Button from '../common/Button'; // Use Button component

function RegisterForm() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [password2, setPassword2] = useState('');
    // Store errors as an object: { fieldName: errorMessage, general?: generalMessage }
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();
    const { addNotification } = useNotification();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErrors({}); // Clear previous errors

        // Basic client-side validation
        if (password !== password2) {
            setErrors({ password2: "Passwords do not match." });
            return;
        }
        if (password.length < 8) {
             setErrors({ password: "Password must be at least 8 characters long." });
             return;
         }
         // Add more client-side validation if needed (e.g., username format)

        setLoading(true);
        try {
            const result = await register(username, email, password, password2);
            if (result.success) {
                console.log("Registration successful");
                addNotification('Registration successful! Please log in.', 'success');
                navigate('/login'); // Redirect to login page after successful registration
            } else {
                // Handle specific field errors or general error from backend
                 if (typeof result.error === 'object' && result.error !== null) {
                    // Map backend error structure (e.g., { email: ["msg"], username: ["msg"] })
                    // to the local errors state.
                    const backendErrors = {};
                    for (const key in result.error) {
                         if (Array.isArray(result.error[key])) {
                             backendErrors[key] = result.error[key].join(' '); // Join array messages
                         } else {
                             backendErrors[key] = result.error[key];
                         }
                    }
                    setErrors(backendErrors);
                    // If no specific field errors, show detail as general error
                    if (Object.keys(backendErrors).length === 0 && result.error.detail) {
                         setErrors({ general: result.error.detail });
                    } else if (Object.keys(backendErrors).length === 0) {
                         setErrors({ general: 'An unknown registration error occurred.' });
                    }

                 } else {
                    // Fallback for non-object errors
                    setErrors({ general: result.error || 'Registration failed. Please try again.' });
                 }
            }
        } catch (err) {
            // Catch unexpected errors during the registration process itself
            console.error("Registration component catch:", err);
            setErrors({ general: 'An unexpected error occurred during registration.' });
        } finally {
            setLoading(false);
        }
    };

     // Helper to get error message for a specific field
     const getFieldError = (fieldName) => errors?.[fieldName];

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
             {/* Display general error messages */}
             {errors?.general && (
                 <p className="text-red-500 dark:text-red-400 text-sm bg-red-100 dark:bg-red-900 p-2 rounded border border-red-300 dark:border-red-700">
                     {errors.general}
                 </p>
             )}
            <div>
                <label htmlFor="register-username" className="block text-sm font-medium text-font-color mb-1">Username</label>
                <input
                    type="text"
                    id="register-username" // Unique ID
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    autoComplete="username"
                    className={`w-full p-2 border rounded bg-background text-font-color focus:outline-none focus:ring-1 disabled:opacity-50 dark:placeholder-gray-500 ${getFieldError('username') ? 'border-red-500 ring-red-500' : 'border-table-border focus:ring-primary'}`}
                    placeholder="Choose a username"
                    disabled={loading}
                />
                 {getFieldError('username') && <p className="text-red-500 text-xs mt-1">{getFieldError('username')}</p>}
            </div>
            <div>
                <label htmlFor="register-email" className="block text-sm font-medium text-font-color mb-1">Email Address</label>
                <input
                    type="email"
                    id="register-email" // Unique ID
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    className={`w-full p-2 border rounded bg-background text-font-color focus:outline-none focus:ring-1 disabled:opacity-50 dark:placeholder-gray-500 ${getFieldError('email') ? 'border-red-500 ring-red-500' : 'border-table-border focus:ring-primary'}`}
                    placeholder="you@example.com"
                    disabled={loading}
                />
                {getFieldError('email') && <p className="text-red-500 text-xs mt-1">{getFieldError('email')}</p>}
            </div>
            <div>
                <label htmlFor="register-password" className="block text-sm font-medium text-font-color mb-1">Password</label>
                <input
                    type="password"
                    id="register-password" // Unique ID
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                     className={`w-full p-2 border rounded bg-background text-font-color focus:outline-none focus:ring-1 disabled:opacity-50 ${getFieldError('password') ? 'border-red-500 ring-red-500' : 'border-table-border focus:ring-primary'}`}
                     placeholder="Choose a strong password (min 8 chars)"
                    disabled={loading}
                />
                 {getFieldError('password') && <p className="text-red-500 text-xs mt-1">{getFieldError('password')}</p>}
            </div>
            <div>
                <label htmlFor="register-password2" className="block text-sm font-medium text-font-color mb-1">Confirm Password</label>
                <input
                    type="password"
                    id="register-password2" // Unique ID
                    value={password2}
                    onChange={(e) => setPassword2(e.target.value)}
                    required
                    autoComplete="new-password"
                    className={`w-full p-2 border rounded bg-background text-font-color focus:outline-none focus:ring-1 disabled:opacity-50 ${getFieldError('password2') ? 'border-red-500 ring-red-500' : 'border-table-border focus:ring-primary'}`}
                    placeholder="Enter your password again"
                    disabled={loading}
                />
                 {getFieldError('password2') && <p className="text-red-500 text-xs mt-1">{getFieldError('password2')}</p>}
            </div>
            <Button
                type="submit"
                variant="primary"
                disabled={loading}
                className="w-full" // Make button full width
            >
                 {loading ? <LoadingSpinner size="sm" color="text-white" /> : 'Register'}
            </Button>
             {/* Link to Login Page */}
             <p className="text-center text-sm text-font-color mt-4">
                 Already have an account?{' '}
                 <Link to="/login" className="text-link-color hover:underline font-medium">
                     Login here
                 </Link>
             </p>
        </form>
    );
}

export default RegisterForm;