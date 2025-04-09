import axios from 'axios';

// Get the API base URL from environment variables, with a fallback for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create a configured axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Crucial for sending session cookies from browser to backend
  headers: {
    'Content-Type': 'application/json', // Default content type for requests
    // 'Accept': 'application/json', // Usually default, but good practice to be explicit
  }
});

// --- CSRF Token Handling ---

// Function to get CSRF token value from cookies
// Django typically names the CSRF cookie 'csrftoken'
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Axios Request Interceptor:
// Automatically attaches the CSRF token (read from cookies) to the headers
// of non-safe HTTP methods (POST, PUT, PATCH, DELETE).
api.interceptors.request.use(
    config => {
        const method = config.method?.toUpperCase();
        // Check if the method requires CSRF protection
        if (method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
            const csrfToken = getCookie('csrftoken');
            // console.debug("Interceptor: Method requires CSRF:", method, config.url);
            if (csrfToken) {
                // Add the token to the request headers
                config.headers['X-CSRFToken'] = csrfToken;
                 // console.debug("Interceptor: Attaching CSRF token:", csrfToken);
            } else {
                 // Warn if token is missing, as the request will likely fail
                 console.warn(`CSRF token not found in cookies for request: ${method} ${config.url}. Request might fail.`);
                 // Consider fetching CSRF token here via getCsrfToken() if missing, although
                 // the initial fetch in AuthContext should ideally handle this.
            }
        }
        return config; // Continue with the modified config
    },
    error => {
        // Handle errors during request setup
        console.error("Axios request interceptor error:", error);
        return Promise.reject(error); // Reject promise on error
    }
);


// Axios Response Interceptor (Optional):
// Can be used for global error handling, like logging out on 401/403 errors.
api.interceptors.response.use(
  response => response, // Pass through successful responses directly
  error => {
    // Log details for failed requests
    // console.error("Axios Response Error:", {
    //     message: error.message,
    //     url: error.config?.url,
    //     method: error.config?.method,
    //     status: error.response?.status,
    //     data: error.response?.data,
    // });

    // --- Example: Global handling for Unauthorized/Forbidden ---
    // if (error.response && (error.response.status === 401 || error.response.status === 403)) {
    //   console.warn(`API Request Unauthorized/Forbidden (${error.response.status}): ${error.config?.method} ${error.config?.url}`);
    //   // **Important**: Avoid direct navigation here. Let AuthContext or components handle it
    //   // based on the error to prevent infinite loops or unexpected redirects.
    //   // E.g., AuthContext's checkAuthStatus might fail, setting isAuthenticated to false,
    //   // which triggers PrivateRoute to redirect to login.
    // }

    // Reject the promise so the calling code's .catch() block is executed
    return Promise.reject(error);
  }
);

// --- API Function Definitions ---
// Group API calls by resource type for better organization.

// -- Authentication --
export const getCsrfToken = () => api.get('/auth/csrf/');
export const loginUser = (email, password) => api.post('/auth/login/', { email, password });
export const registerUser = (username, email, password, password2) => api.post('/auth/register/', { username, email, password, password2 });
export const logoutUser = () => api.post('/auth/logout/');
export const checkAuth = () => api.get('/auth/status/');

// -- Pages --
export const getPages = (config) => api.get('/pages/', config); // Pass optional config (e.g., signal)
export const createPage = (data, config) => api.post('/pages/', data, config); // data = { name: "..." }
export const getPageDetail = (slug, config) => api.get(`/pages/${slug}/`, config); // Fetches metadata + columns
export const deletePage = (slug, config) => api.delete(`/pages/${slug}/`, config);
export const updatePageMetadata = (slug, data, config) => api.patch(`/pages/${slug}/`, data, config); // For name updates etc.

// -- Page Data & Structure --
export const getPageData = (slug, config) => api.get(`/pages/${slug}/data/`, config); // Fetches columns, rows, cells
export const savePageData = (slug, data, config) => api.post(`/pages/${slug}/save/`, data, config); // data = { columns, rows, commit_message? }
export const updateColumnWidths = (slug, updates, config) => api.post(`/pages/${slug}/columns/width/`, { updates }, config); // updates = [{id, width}, ...]

// -- Page Versions --
export const getPageVersions = (slug, config) => api.get(`/pages/${slug}/versions/`, config);

// -- Todos --
export const getTodos = (config) => api.get('/todos/', config); // Lists accessible ToDos
export const createTodo = (data, config) => api.post('/todos/', data, config); // { name, is_personal, source_page_slug }
export const getTodoDetail = (todoId, config) => api.get(`/todos/${todoId}/`, config); // Includes source page info & statuses
export const deleteTodo = (todoId, config) => api.delete(`/todos/${todoId}/`, config);
export const updateTodoStatus = (todoId, rowId, status, config) => api.patch(`/todos/${todoId}/status/${rowId}/`, { status }, config);

// Add functions for Groups and Permissions API calls later if needed
// export const getGroups = (config) => api.get('/groups/', config);
// export const getPagePermissions = (slug, config) => api.get(`/pages/${slug}/permissions/`, config);
// export const grantPagePermission = (slug, data, config) => api.post(`/pages/${slug}/permissions/`, data, config);

// Export the configured axios instance as default for direct use if needed
export default api;