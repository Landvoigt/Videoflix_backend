@echo off
SET PGPASSWORD=your_password_here
REM Set the database connection details
SET DB_NAME=your_db_name
SET DB_USER=your_db_user
SET DB_HOST=your_db_host
SET DB_PORT=your_db_port

REM Dump the current database to a file
pg_dump -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -F c -b -v -f db_backup.dump %DB_NAME%

REM Pull the latest changes from git
git pull

REM Restore the database from the dumped file
pg_restore -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -d %DB_NAME% -v db_backup.dump
