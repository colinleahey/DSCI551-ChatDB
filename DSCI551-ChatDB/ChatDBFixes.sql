CREATE DATABASE IF NOT EXISTS movielens_db;
USE movielens_db;

DROP TABLE IF EXISTS movie_genres;
DROP TABLE IF EXISTS movies_clean;

show tables;

# To allow for foreign key constraint for movie_genres
ALTER TABLE movies_clean ADD PRIMARY KEY (movieid);

CREATE TABLE movie_genres (
    `movieid` INT,
    `genre` VARCHAR(255),
    FOREIGN KEY (`movieid`) REFERENCES `movies_clean`(`movieid`)
);

SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
