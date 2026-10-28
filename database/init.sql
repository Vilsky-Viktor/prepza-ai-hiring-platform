-- Runs only when the postgres volume is created. For an existing volume, create new
-- databases by hand: docker-compose exec postgres createdb -U prepza <name>
-- The admin (prepza) makes them; the db-roles service then gives each to its service's own user
-- (compose/services.yml), as the db-roles job does in production.
CREATE DATABASE library;
CREATE DATABASE generation;
CREATE DATABASE rounds;
CREATE DATABASE companies;
CREATE DATABASE billing;
CREATE DATABASE notifications;
CREATE DATABASE ats;
CREATE DATABASE api;
CREATE DATABASE assistant;
CREATE DATABASE accounts;
CREATE DATABASE site;

-- pgvector isn't a trusted extension, so library's own user can't create it: the admin does,
-- and library's migration finds it there (as in production, where the admin made it first).
\connect library
CREATE EXTENSION IF NOT EXISTS vector;
