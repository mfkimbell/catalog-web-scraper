#!/bin/bash


echo "Creating database: postgres"
psql -U postgres -c "CREATE DATABASE postgres";

echo "Running tables.sql"
psql -d postgres -U postgres -f ./tables.sql.init



