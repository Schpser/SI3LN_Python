# Frontend Dockerfile for SI3LN Web Dashboard (v2 — cross-browser)
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm -rf /usr/share/nginx/html/*

# Ensure correct MIME types for WASM (cross-browser compat)
RUN echo 'application/wasm wasm;' >> /etc/nginx/mime.types && \
    echo 'application/javascript mjs;' >> /etc/nginx/mime.types

# Copy web dashboard files
COPY . /usr/share/nginx/html/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost/ || exit 1

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
