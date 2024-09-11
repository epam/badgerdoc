FROM nginx:1.27-bookworm
COPY nginx.conf /etc/nginx/nginx.conf
COPY routes.conf /etc/nginx/conf.d/routes.conf
EXPOSE 8080
ENTRYPOINT ["/docker-entrypoint.sh"]
STOPSIGNAL SIGQUIT
CMD ["nginx", "-g", "daemon off;"]
