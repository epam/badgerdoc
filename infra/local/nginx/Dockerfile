FROM nginx:1.25-alpine

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Create directory for static files
RUN mkdir -p /var/www/staticfiles

# Set proper permissions
RUN chown -R nginx:nginx /var/www/staticfiles

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
