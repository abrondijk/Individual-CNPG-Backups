from datetime import datetime, timedelta
import os
import sys
import psycopg2
from sh import pg_dump

# Retention rules
DAILY_RETENTION = 2
WEEKLY_RETENTION = 2
MONTHLY_RETENTION = 2

DATE_FORMAT = "%Y-%m-%d"

# Postgres credentials
POSTGRES_HOST = ""
POSTGRES_PORT = "5432"
POSTGRES_USER = "postgres"
POSTGRES_PASS = "password"

# Postgres backup path
BACKUP_PATH = "/backup"

# Postgres database backup exceptions
DATABASE_EXCEPTIONS = []

BACKUP_FILE_EXTENSION = ".dump"


def print_error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def files_to_dates(database, files):
    dates = []

    date_length = len(datetime.now().strftime(DATE_FORMAT))
    file_extension_length = len(BACKUP_FILE_EXTENSION)
    prefix_length = len(f"{database}_")

    backup_file_length = prefix_length + date_length + file_extension_length

    # Convert list of file objects to list of datetime objects
    for file in files:
        # Check if the file is a valid backup file, if not skip
        if not len(file) == backup_file_length:
            continue

        date_str = file[prefix_length:-file_extension_length]

        # Check if the date is valid
        try:
            date = datetime.strptime(date_str, DATE_FORMAT)
            dates.append(date)
        except ValueError:
            continue

    return dates


def dates_to_files(database, dates):
    return [f"{database}_{date.strftime(DATE_FORMAT)}{BACKUP_FILE_EXTENSION}" for date in dates]


def backup_retention(database):
    # Check if subdirectory exists
    if not os.path.exists(f"{BACKUP_PATH}/{database}"):
        return [], []

    # Get list of dates from the files in the subdirectory
    backup_dates = files_to_dates(database, os.listdir(f"{BACKUP_PATH}/{database}"))

    # Sort dates from new to old
    backup_dates.sort(reverse=True)

    found_daily = 0
    found_weekly = 0
    found_monthly = 0

    retained_dates = backup_dates.copy()
    discarded_dates = []

    today = datetime.now()

    for date in backup_dates:
        # Mondays
        if found_weekly < WEEKLY_RETENTION and date.weekday() == 0:
            found_weekly += 1
        # First day of the month
        elif found_monthly < MONTHLY_RETENTION and date.day == 1:
            found_monthly += 1
        # Days between today and DAILY_RETENTION days ago
        elif found_daily < DAILY_RETENTION and today - timedelta(days=DAILY_RETENTION) <= date <= today:
            found_daily += 1
        # If date is not to be retained
        else:
            retained_dates.remove(date)
            discarded_dates.append(date)

    if len(discarded_dates):
        print(f"Deleting backups for {database}:")
        # Delete the discarded files
        for file in dates_to_files(database, discarded_dates):
            print(f"\t{file}")
            os.remove(f"{BACKUP_PATH}/{database}/{file}")

    return dates_to_files(database, retained_dates), dates_to_files(database, discarded_dates)


def get_all_databases():
    conn = None
    databases = []
    try:
        conn = psycopg2.connect(host=POSTGRES_HOST, port=POSTGRES_PORT, user=POSTGRES_USER,
                                password=POSTGRES_PASS, dbname='postgres')
        cursor = conn.cursor()
        cursor.execute('SELECT datname FROM pg_database WHERE datistemplate = false;')
        query_result = cursor.fetchall()

        # Convert the list of tuples to a list of strings
        query_result = [t[0] for t in query_result]

        # Remove the databases from the exceptions list
        databases = [database for database in query_result if database not in DATABASE_EXCEPTIONS]

    except psycopg2.DatabaseError as e:
        print_error('Error: %s' % e)
        sys.exit(1)
    finally:
        if conn:
            conn.close()

    return databases


def database_backup(database):
    # Create the backup location
    backup_location = f'{BACKUP_PATH}/{database}'
    os.makedirs(backup_location, exist_ok=True)

    # Backup the database
    filename = f'{backup_location}/{database}_{datetime.now().strftime(DATE_FORMAT)}{BACKUP_FILE_EXTENSION}'
    with open(filename, 'wb') as file:
        # Set the password environment variable for the pg_dump command
        os.environ["PGPASSWORD"] = POSTGRES_PASS
        pg_dump('-h', POSTGRES_HOST, '-p', POSTGRES_PORT, '-U', POSTGRES_USER, '-Fc', database, _out=file)


def main():
    global DAILY_RETENTION, WEEKLY_RETENTION, MONTHLY_RETENTION, DATE_FORMAT
    global POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASS
    global BACKUP_PATH
    global DATABASE_EXCEPTIONS

    # Set all the environment variables
    DAILY_RETENTION = int(os.environ.get('DAILY_RETENTION', DAILY_RETENTION))
    WEEKLY_RETENTION = int(os.environ.get('WEEKLY_RETENTION', WEEKLY_RETENTION))
    MONTHLY_RETENTION = int(os.environ.get('MONTHLY_RETENTION', MONTHLY_RETENTION))
    DATE_FORMAT = os.environ.get('TIME_FORMAT', DATE_FORMAT)

    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', POSTGRES_PORT))
    POSTGRES_USER = os.environ.get('POSTGRES_USER', POSTGRES_USER)
    POSTGRES_PASS = os.environ.get('POSTGRES_PASS')
    if POSTGRES_HOST is None or POSTGRES_PASS is None:
        print_error("Please provide the Postgres credentials")
        sys.exit(os.EX_USAGE)

    BACKUP_PATH = os.environ.get('BACKUP_PATH', BACKUP_PATH)

    exceptions = os.environ.get('DATABASE_EXCEPTIONS', DATABASE_EXCEPTIONS)
    DATABASE_EXCEPTIONS = exceptions.split(",") if exceptions else []

    databases = get_all_databases()

    for database in databases:
        database_backup(database)
        backup_retention(database)


if __name__ == "__main__":
    main()
