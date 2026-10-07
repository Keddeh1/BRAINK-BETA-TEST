FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY vfs_server /app/vfs_server
RUN useradd --system --uid 10001 --create-home vfs \
    && mkdir -p /var/lib/keddeh-vfs \
    && chown -R vfs:vfs /var/lib/keddeh-vfs
USER vfs
EXPOSE 8787
ENTRYPOINT ["python","-m","vfs_server.server"]
CMD ["--root","/var/lib/keddeh-vfs","--host","127.0.0.1","--port","8787"]
