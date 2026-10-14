-- reverse: create index "unique_roles_users" to table: "roles_users"
DROP INDEX `unique_roles_users`;
-- reverse: create "roles_users" table
DROP TABLE `roles_users`;
-- reverse: create index "idx_session_type_status" to table: "sessions"
DROP INDEX `idx_session_type_status`;
-- reverse: create index "idx_session_type" to table: "sessions"
DROP INDEX `idx_session_type`;
-- reverse: create index "idx_session_user_status" to table: "sessions"
DROP INDEX `idx_session_user_status`;
-- reverse: create index "idx_session_status" to table: "sessions"
DROP INDEX `idx_session_status`;
-- reverse: create index "idx_session_expires_at" to table: "sessions"
DROP INDEX `idx_session_expires_at`;
-- reverse: create index "idx_session_user_id" to table: "sessions"
DROP INDEX `idx_session_user_id`;
-- reverse: create "sessions" table
DROP TABLE `sessions`;
-- reverse: create "files" table
DROP TABLE `files`;
-- reverse: create index "idx_user_email" to table: "users"
DROP INDEX `idx_user_email`;
-- reverse: create index "idx_user_username" to table: "users"
DROP INDEX `idx_user_username`;
-- reverse: create index "idx_user_provider_provider_id" to table: "users"
DROP INDEX `idx_user_provider_provider_id`;
-- reverse: create "users" table
DROP TABLE `users`;
-- reverse: create "permissions" table
DROP TABLE `permissions`;
-- reverse: create index "roles_name_key" to table: "roles"
DROP INDEX `roles_name_key`;
-- reverse: create "roles" table
DROP TABLE `roles`;
-- reverse: create index "idx_activity_created" to table: "_activities"
DROP INDEX `idx_activity_created`;
-- reverse: create index "idx_activity_actor_created" to table: "_activities"
DROP INDEX `idx_activity_actor_created`;
-- reverse: create index "idx_activity_schema_record" to table: "_activities"
DROP INDEX `idx_activity_schema_record`;
-- reverse: create "_activities" table
DROP TABLE `_activities`;
-- reverse: create index "migrations_version_key" to table: "migrations"
DROP INDEX `migrations_version_key`;
-- reverse: create "migrations" table
DROP TABLE `migrations`;
