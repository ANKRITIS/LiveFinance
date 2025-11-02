# frontend/Dockerfile
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install
RUN npm rebuild esbuild

COPY . .

# Expose the Vite port
EXPOSE 5173

# IMPORTANT: Host 0.0.0.0 is required for Docker to expose the port
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]