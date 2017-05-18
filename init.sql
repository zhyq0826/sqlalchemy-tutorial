drop database IF EXISTS `sqlalchemy_lab`;

create database if not EXISTS `sqlalchemy_lab`;

ALTER database `sqlalchemy_lab` CHARACTER SET utf8mb4;

SET character_set_client = utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_database = utf8mb4;
SET character_set_results = utf8mb4;
SET character_set_server = utf8mb4;

SET collation_connection = utf8_general_ci;
SET collation_database = utf8_general_ci;
SET collation_server = utf8_general_ci;

use sqlalchemy_lab;


create table if not EXISTS tag (
    id bigint  not null auto_increment primary key,
    name varchar(255) not null,
    group_id bigint not null
);