-- create "migrations" table
CREATE TABLE `migrations` (`id` uuid NOT NULL, `version` text NOT NULL, `name` text NULL, `applied_at` datetime NOT NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `updated_at` datetime NULL, `deleted_at` datetime NULL, PRIMARY KEY (`id`));
-- create index "migrations_version_key" to table: "migrations"
CREATE UNIQUE INDEX `migrations_version_key` ON `migrations` (`version`);
-- create "_activities" table
CREATE TABLE `_activities` (`id` uuid NOT NULL, `actor_id` uuid NULL, `actor_type` text NULL, `action` text NULL, `schema_name` text NULL, `record_id` text NULL, `ip` text NULL, `method` text NULL, `path` text NULL, `trace_id` text NULL, `changed_keys` text NULL, `changes` text NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `updated_at` datetime NULL, `deleted_at` datetime NULL, PRIMARY KEY (`id`));
-- create index "idx_activity_schema_record" to table: "_activities"
CREATE INDEX `idx_activity_schema_record` ON `_activities` (`schema_name`, `record_id`);
-- create index "idx_activity_actor_created" to table: "_activities"
CREATE INDEX `idx_activity_actor_created` ON `_activities` (`actor_id`, `created_at`);
-- create index "idx_activity_created" to table: "_activities"
CREATE INDEX `idx_activity_created` ON `_activities` (`created_at`);
-- create "roles" table
CREATE TABLE `roles` (`id` uuid NOT NULL, `name` text NOT NULL, `description` text NULL, `root` bool NULL, `system` bool NULL, `rule` text NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `updated_at` datetime NULL, `deleted_at` datetime NULL, PRIMARY KEY (`id`));
-- create index "roles_name_key" to table: "roles"
CREATE UNIQUE INDEX `roles_name_key` ON `roles` (`name`);
-- create "permissions" table
CREATE TABLE `permissions` (`id` uuid NOT NULL, `resource` text NOT NULL, `value` text NOT NULL, `modifier` json NULL, `role_id` uuid NOT NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `updated_at` datetime NULL, `deleted_at` datetime NULL, PRIMARY KEY (`id`), CONSTRAINT `permission_role_id` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON UPDATE NO ACTION ON DELETE NO ACTION);
-- create "users" table
CREATE TABLE `users` (`id` uuid NOT NULL, `username` text NULL, `email` text NULL, `first_name` text NULL, `last_name` text NULL, `bio` text NULL, `password` text NULL, `active` bool NULL, `provider` text NULL, `provider_id` text NULL, `provider_username` text NULL, `provider_profile_image` text NULL, `avatar_id` uuid NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `updated_at` datetime NULL, `deleted_at` datetime NULL, PRIMARY KEY (`id`), CONSTRAINT `user_avatar_id` FOREIGN KEY (`avatar_id`) REFERENCES `files` (`id`) ON UPDATE NO ACTION ON DELETE SET NULL);
-- create index "idx_user_provider_provider_id" to table: "users"
CREATE UNIQUE INDEX `idx_user_provider_provider_id` ON `users` (`provider`, `provider_id`);
-- create index "idx_user_username" to table: "users"
CREATE UNIQUE INDEX `idx_user_username` ON `users` (`username`);
-- create index "idx_user_email" to table: "users"
CREATE UNIQUE INDEX `idx_user_email` ON `users` (`email`);
-- create "files" table
CREATE TABLE `files` (`id` uuid NOT NULL, `disk` text NOT NULL, `name` text NOT NULL, `path` text NOT NULL, `type` text NOT NULL, `size` integer NOT NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `owner_id` uuid NOT NULL, `updated_at` datetime NULL, `deleted_at` datetime NULL, PRIMARY KEY (`id`), CONSTRAINT `file_owner_id` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON UPDATE NO ACTION ON DELETE NO ACTION);
-- create "sessions" table
CREATE TABLE `sessions` (`id` uuid NOT NULL, `user_id` uuid NOT NULL, `device_info` text NULL, `ip_address` text NULL, `last_activity_at` datetime NULL, `status` text NULL, `expires_at` datetime NOT NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `deleted_at` datetime NULL, `type` text NULL, `otp_hash` text NULL, `otp_attempts` integer NULL, `updated_at` datetime NULL, PRIMARY KEY (`id`));
-- create index "idx_session_user_id" to table: "sessions"
CREATE INDEX `idx_session_user_id` ON `sessions` (`user_id`);
-- create index "idx_session_expires_at" to table: "sessions"
CREATE INDEX `idx_session_expires_at` ON `sessions` (`expires_at`);
-- create index "idx_session_status" to table: "sessions"
CREATE INDEX `idx_session_status` ON `sessions` (`status`);
-- create index "idx_session_user_status" to table: "sessions"
CREATE INDEX `idx_session_user_status` ON `sessions` (`user_id`, `status`);
-- create index "idx_session_type" to table: "sessions"
CREATE INDEX `idx_session_type` ON `sessions` (`type`);
-- create index "idx_session_type_status" to table: "sessions"
CREATE INDEX `idx_session_type_status` ON `sessions` (`type`, `status`);
-- create "roles_users" table
CREATE TABLE `roles_users` (`roles` uuid NOT NULL, `users` uuid NOT NULL, `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP), `updated_at` datetime NULL, `deleted_at` datetime NULL, CONSTRAINT `roles_users_roles` FOREIGN KEY (`roles`) REFERENCES `roles` (`id`) ON UPDATE CASCADE ON DELETE CASCADE, CONSTRAINT `roles_users_users` FOREIGN KEY (`users`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE CASCADE);
-- create index "unique_roles_users" to table: "roles_users"
CREATE UNIQUE INDEX `unique_roles_users` ON `roles_users` (`roles`, `users`);
