FROM fholzer/nginx-brotli

# Copy nginx configuration
COPY ./deployment/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built Svelte app
COPY chat-ui/build/ /usr/share/nginx/html/

ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
