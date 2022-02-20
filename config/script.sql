-- CREATE DATABASE "elipcode-tracker";

-- CREATE SCHEMA "user";
-- CREATE SCHEMA torrent;

---------------------------------------------------------------------------------------------------------

create table "user".permission
(
    id      bigserial primary key,
    name    varchar(100) unique,
    "group" varchar(50)
);
alter table "user".permission
    owner to postgres;

create table "user".rol
(
    id   bigserial primary key,
    name varchar(50) unique
);
alter table "user".rol
    owner to postgres;

create table "user".rol_permission
(
    id            bigserial primary key,
    rol_id        bigint not null,
    permission_id bigint not null,
    constraint rol_permission_rol_id_fkey FOREIGN KEY (rol_id) references "user".rol (id),
    constraint rol_permission_permission_id_fkey FOREIGN KEY (permission_id) references "user".permission (id)
);
alter table "user".rol_permission
    owner to postgres;

create table "user".user
(
    id            bigserial primary key,
    username      varchar(30) unique,
    password      varchar(300),
    email         varchar(50) unique,
    passkey       varchar(100),
    status        varchar(50),
    uploaded      bigint             default 0,
    downloaded    bigint             default 0,
    user_create   varchar(30),
    date_create   timestamp not null default now(),
    user_modifier varchar(30),
    date_modifier timestamp
);
alter table "user".user
    owner to postgres;

create table "user".friendships
(
    id         bigserial primary key,
    userone_id bigint,
    usertwo_id bigint,
    accepted   boolean,
    constraint friendships_userone_id_fkey FOREIGN KEY (userone_id) references "user".user (id),
    constraint friendships_usertwo_id_fkey FOREIGN KEY (usertwo_id) references "user".user (id)
);
alter table "user".friendships
    owner to postgres;

create table "user".rol_user
(
    id      bigserial primary key,
    rol_id  bigint,
    user_id bigint,
    constraint rol_user_rol_id_fkey FOREIGN KEY (rol_id) references "user".rol (id),
    constraint rol_user_user_id_fkey FOREIGN KEY (user_id) references "user".user (id)
);
alter table "user".rol_user
    owner to postgres;

---------------------------------------------------------------------------------------------------------

create table torrent.category
(
    id         bigserial primary key,
    name       varchar(20) not null,
    image_path varchar(300)
);
alter table torrent.category
    owner to postgres;

create table torrent.torrent
(
    id             bigserial primary key,
    info_hash      varchar,
    name           varchar(300),
    url            varchar,
    description    text,
    info           bytea,
    download_count integer default 0,
    seeders        integer default 0,
    leechers       integer default 0,
    last_checked   timestamp,
    uploaded_time  timestamp,
    uploaded_user  varchar(30)
);
alter table torrent.torrent
    owner to postgres;

create table torrent.torrent_category
(
    id          bigserial primary key,
    principal   boolean not null default false,
    torrent_id  bigint,
    category_id bigint,
    constraint torrent_category_torrent_id_fkey FOREIGN KEY (torrent_id) references torrent.torrent (id),
    constraint torrent_category_category_id_fkey FOREIGN KEY (category_id) references torrent.category (id)
);
alter table torrent.torrent_category
    owner to postgres;

create table torrent.torrent_file
(
    id          bigserial primary key,
    torrent_id  bigint,
    module      varchar(15),
    principal   boolean   not null default false,
    file_name   varchar,
    mime_type   varchar(100),
    path        varchar(300),
    user_create varchar(30),
    date_create timestamp not null default now(),
    constraint torrent_category_torrent_id_fkey FOREIGN KEY (torrent_id) references torrent.torrent (id)
);
alter table torrent.torrent_file
    owner to postgres;

create table torrent.peers
(
    id               bigserial primary key,
    peer_id          varchar,
    torrent_id       bigint,
    user_id          bigint,
    ip               varchar,
    port             integer,
    active           boolean,
    uploaded         bigint  default 0,
    downloaded       bigint  default 0,
    uploaded_total   bigint  default 0,
    downloaded_total bigint  default 0,
    seeding          boolean default false,
    constraint peers_torrent_id_fkey FOREIGN KEY (torrent_id) references torrent.torrent (id),
    constraint peers_user_id_fkey FOREIGN KEY (user_id) references "user".user (id)
);
alter table torrent.peers
    owner to postgres;

