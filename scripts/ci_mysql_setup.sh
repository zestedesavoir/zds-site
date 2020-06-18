#!/bin/bash

sudo sed -i'' 's/\[mysqld\]/\[mysqld\]\ninnodb_file_per_table=on\ninnodb_file_format=barracuda\ninnodb_large_prefix=on\ncharacter-set-client-handshake=false\ncharacter-set-server=utf8mb4\ncollation-server=utf8mb4_unicode_ci/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql

# Travis should fail as soon as possible
sudo mysql -u root -e "SET GLOBAL sql_mode = 'NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES';"

# Avoid "mysql has gone away" errors
sudo mysql -u root -e "SET GLOBAL wait_timeout = 36000;"
sudo mysql -u root -e "SET GLOBAL max_allowed_packet = 134209536;"

# Ensures correct charset and collation
sudo mysql -u root -e "SET GLOBAL character_set_server = 'utf8mb4';"
sudo mysql -u root -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci';"

# Ensures the root user is able to connect without password
sudo mysql -u root -e "SET Password=PASSWORD('')"

# Create database with the correct charset and collation
sudo mysql -u root -e "CREATE DATABASE zds_test CHARACTER SET = 'utf8mb4' COLLATE = 'utf8mb4_unicode_ci';"
