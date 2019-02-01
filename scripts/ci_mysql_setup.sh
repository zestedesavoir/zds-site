#!/bin/bash

function print_info {
    echo -n -e "\033[0;36m";
    echo "$1";
    echo -n -e "\033[00m";
}

if [[ "$ZDS_TEST_JOB" == *"zds."* ]] || [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
    #display print_info
    forwho=""
    if [[ "$ZDS_TEST_JOB" == *"zds."* ]]; then
        forwho="'zds.*' tasks (-> needed for tests)"

        if [[ "$ZDS_TEST_JOB" == *"selenium"* ]]; then
            forwho="$forwho and selenium"
        fi
    else
        forwho="selenium"
    fi
    print_info "* Install mysql for $forwho."

    #install

    set -ex

    sudo sed -i'' 's/\[client\]/\[client\]\ndefault-character-set=utf8mb4/' /etc/mysql/my.cnf
    sudo sed -i'' 's/\[mysql\]/\[mysql\]\ndefault-character-set=utf8mb4/' /etc/mysql/my.cnf
    sudo sed -i'' 's/\[mysqld\]/\[mysqld\]\ninnodb_file_per_table=on\ninnodb_file_format=barracuda\ninnodb_large_prefix=on\ncharacter-set-client-handshake=false\ncharacter-set-server=utf8mb4\ncollation-server=utf8mb4_unicode_ci/' /etc/mysql/my.cnf
    sudo /etc/init.d/mysql restart
    # Travis should fail as soon as possible
    mysql -u root -e "SET GLOBAL sql_mode = 'NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES';"
    # Avoid "mysql has gone away" errors
    mysql -u root -e "SET GLOBAL wait_timeout = 36000;"
    mysql -u root -e "SET GLOBAL max_allowed_packet = 134209536;"
    # Create database with the correct charset and collation
    mysql -u root -e "CREATE DATABASE zds_test CHARACTER SET = utf8mb4 COLLATE utf8mb4_unicode_ci;"
fi
