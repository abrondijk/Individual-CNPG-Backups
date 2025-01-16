# Individual Postgres Backups

This script is used to back up individual Postgres databases. It is intended to be run as a cron job.

Its main purpose is to back up individual databases for CNPG, as that only allows for full backups of all databases.
This way, only a specific database can be restored if necessary.

## Usage

The script is intended to be run as a cron job. It will connect to the specified Postgres server and backup all the databases that are on the server (except for the databases in the `DATABASE_EXCEPTIONS` environment variable).

First, the script will delete any backups that are older than the retention period (specified in environment variables).
The script will create a new directory for each database in the `BACKUP_DIR` directory. It will then perform a `pg_dump` on the database and save the output to a gzipped file in the directory.

## Environment Variables

| Variable              | Default value | Purpose                                                                        |
|-----------------------|---------------|--------------------------------------------------------------------------------|
| `BACKUP_PATH`         | `/backup`     | Directory to where the `pg_dump` files are written to.                         |
| `DATABASE_EXCEPTIONS` |               | A comma seperated list of database to skip backing up.                         |
| `DATE_FORMAT`         | `%Y-%m-%d`    | Optionally change the format of the date that will be in the backup filenames. |
| `DAILY_RETENTION`     | 2             | Number of backups daily backups to retain.                                     |
| `WEEKLY_RETENTION`    | 2             | Number of weeks to retain that weeks backup made on Monday.                    |
| `MONTHLY_RETENTION`   | 2             | Number of months to retain that months backup made on the 1st.                 |
| `POSTGRES_HOST`       |               | IP address or hostname of the Postgres server                                  |
| `POSTGRES_PORT`       | 5432          | Postgres port                                                                  |
| `POSTGRES_USER`       | postgres      | User to authenticate with                                                      |
| `POSTGRES_PASS`       |               | Password to authenticate with                                                  |
