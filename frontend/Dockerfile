# Use Node.js 20 with full build tools
FROM node:20-bullseye

# Set working directory
WORKDIR /app/frontend

# Install system dependencies and update npm
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g npm@latest

# Copy package files first
COPY package*.json ./

# Install main dependencies first (this includes @sveltejs/adapter-node)
RUN npm cache clean --force && \
    npm install --include=dev --legacy-peer-deps

# Copy source code
COPY . .

# Build the application for production
RUN npm run build

# Expose port
EXPOSE 3000

# Start the Node.js application
CMD ["node", "build"]
