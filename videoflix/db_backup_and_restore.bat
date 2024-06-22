@echo off
SET PGPASSWORD=videoflix12345
REM Set the database connection details
SET DB_NAME=videoflix_backend
SET DB_USER=videoflix_admin
SET DB_HOST=localhost
SET DB_PORT=5432

REM Dump the current database to a file
pg_dump -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -F c -b -v -f db_backup.dump %DB_NAME%

REM Pull the latest changes from git
git pull

REM Restore the database from the dumped file
pg_restore -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -v db_backup.dump


