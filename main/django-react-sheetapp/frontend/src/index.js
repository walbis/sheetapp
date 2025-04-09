import React from 'react';
import ReactDOM from 'react-dom/client'; // Use new React 18 createRoot API
import './styles/index.css'; // Import global styles (including Tailwind and CSS variables)
import App from './App'; // Import the main application component
import reportWebVitals from './reportWebVitals';
import { BrowserRouter } from 'react-router-dom'; // Router provider
import { ThemeProvider } from './contexts/ThemeContext'; // Theme context provider
import { AuthProvider } from './contexts/AuthContext'; // Authentication context provider
import { NotificationProvider } from './contexts/NotificationContext'; // Notification context provider

// Get the root DOM element where the React app will be mounted
const rootElement = document.getElementById('root');

// Create a React root using the new Concurrent Mode API
const root = ReactDOM.createRoot(rootElement);

// Render the application
root.render(
  // StrictMode helps catch potential problems in an application during development
  <React.StrictMode>
    {/* BrowserRouter provides routing capabilities to the entire app */}
    <BrowserRouter>
      {/* ThemeProvider manages light/dark theme state */}
      <ThemeProvider>
        {/* NotificationProvider manages global notifications */}
        <NotificationProvider>
          {/* AuthProvider manages user authentication state and actions */}
          <AuthProvider>
            {/* The main App component containing all routes and views */}
            <App />
          </AuthProvider>
        </NotificationProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();