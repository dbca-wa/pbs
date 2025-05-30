## Step 1: Use pbs_django_3 Branch of PBS.
```

PBS Segregated branch: https://github.com/dbca-wa/pbs/tree/pbs_django_3

```


## Step 2: Create new database and restore it with copy of Production PBS database.
```

CREATE DATABASE pbs_dev;
CREATE USER pbs_dev WITH PASSWORD '<password>';
GRANT ALL PRIVILEGES ON DATABASE "pbs_dev" to pbs_dev;
\c pbs_dev
create extension postgis;
GRANT ALL ON ALL TABLES IN SCHEMA public TO pbs_dev;
GRANT ALL ON SCHEMA public TO pbs_dev;

```

## Step 3: Create ENV file as per the production PBS.
```



```

## Step 4: install packages
```
pip install -r requirements.txt
```

## Step 4: Drop the reversion tables (take a backup before dropping them)
```
pg_dump -U pbsv1_dev -W  -h d253c25458aa.oimpguat01.private.postgres.database.azure.com -d pbsv1_dev -t reversion_revision -t reversion_revision -F c -f /dbdumps/pbs_dev_reversion_record_backup.sql

```
Connect to database using psql.

```
DROP table reversion_version;
DROP table reversion_revision;

```

## Step 5: Fake the following migrations
```

admin
 0001_initial

guardian
 0001_initial

tastypie
 0001_initial

document
 0001_initial
 0002_initial

implementation
 0001_initial
 0002_initial

pbs
 0001_initial
 0002_initial

prescription
 0001_initial
 0002_initial

Operations to perform:
  Target specific migration: 0002_initial, from prescription
Running migrations:
  Applying risk.0001_initial... FAKED
  Applying prescription.0002_initial... FAKED

report
 0001_initial

review
 0001_initial

sessions
 0001_initial

stakeholder
 0001_initial

```

## Step 7: Apply the remaining migrations

```
./manage.py migrate admin
./manage.py migrate auth
./manage.py migrate guardian
./manage.py migrate tastypie
./manage.py migrate reversion
./manage.py migrate

```


