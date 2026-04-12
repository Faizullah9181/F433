FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 5173

# Run dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
