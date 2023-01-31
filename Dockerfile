FROM cfrl/postgres-base:14

COPY ./tables.sql /docker-entrypoint-initdb.d/tables.sql.init

COPY ./init_db.sh /docker-entrypoint-initdb.d/init_db.sh

WORKDIR /docker-entrypoint-initdb.d 
RUN chown -R postgres:postgres /docker-entrypoint-initdb.d && \
    chmod -R 755 /docker-entrypoint-initdb.d

EXPOSE 5432

