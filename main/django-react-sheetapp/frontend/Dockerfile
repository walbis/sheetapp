# File: django-react-sheetapp/frontend/Dockerfile
# Use node for development and build stage
FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies - use legacy peer deps if needed
# Use npm ci for potentially faster/more reliable installs if lock file is solid
RUN npm install --legacy-peer-deps

# Copy the rest of the application code
# Files specified in .dockerignore will be excluded
COPY . .

# Expose the React development server port
EXPOSE 3000

# Default command to run when the container starts
# This will be overridden by docker-compose's 'command: npm start'
# but it's good practice to have a default.
CMD ["npm", "start"]
