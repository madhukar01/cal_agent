FROM fholzer/nginx-brotli

COPY nginx.conf /etc/nginx/conf.d/default.conf
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
