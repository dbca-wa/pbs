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

./manage.py migrate admin 0001_initial --fake

Output:
Operations to perform:
  Target specific migration: 0001_initial, from admin
Running migrations:
  Applying contenttypes.0001_initial... FAKED
  Applying auth.0001_initial... FAKED
  Applying admin.0001_initial... FAKED




guardian
 0001_initial

 ./manage.py migrate guardian 0001_initial --fake

 Output:
 Operations to perform:
  Target specific migration: 0001_initial, from guardian
Running migrations:
  Applying guardian.0001_initial... FAKED

tastypie
 0001_initial

 ./manage.py migrate tastypie 0001_initial --fake

 output:
 Operations to perform:
  Target specific migration: 0001_initial, from tastypie
Running migrations:
  Applying tastypie.0001_initial... FAKED


document
 0001_initial
 ./manage.py migrate document 0001_initial --fake

 0002_initial
 ./manage.py migrate document 0002_initial --fake

 Output:
 Operations to perform:
  Target specific migration: 0002_initial, from document
Running migrations:
  Applying prescription.0001_initial... FAKED
  Applying document.0002_initial... FAKED

implementation
 0001_initial
 ./manage.py migrate implementation 0001_initial --fake
 0002_initial
 ./manage.py migrate implementation 0002_initial --fake

pbs
 0001_initial
 ./manage.py migrate pbs 0001_initial --fake
 0002_initial
 ./manage.py migrate pbs 0002_initial --fake

prescription
 0002_initial
 ./manage.py migrate prescription 0002_initial --fake

Operations to perform:
  Target specific migration: 0002_initial, from prescription
Running migrations:
  Applying risk.0001_initial... FAKED
  Applying prescription.0002_initial... FAKED

report
 0001_initial
 ./manage.py migrate report 0001_initial --fake

review
 0001_initial
 ./manage.py migrate review 0001_initial --fake

sessions
 0001_initial
 ./manage.py migrate sessions 0001_initial --fake

stakeholder
 0001_initial
 ./manage.py migrate stakeholder 0001_initial --fake



```

## Step 6: Apply the remaining migrations

```
./manage.py migrate admin
./manage.py migrate auth
./manage.py migrate guardian
./manage.py migrate tastypie
./manage.py migrate reversion
./manage.py migrate

```
## Step 7: Apply the script to change the EndorsingRole disclaimer text (change word 'DPaW' to 'department).
  Do the dry run first to check if 9 records are changing then run the script to apply the change.
  ```
  python pbs/scripts/update_endorsingrole_disclaimers.py --dry-run
  python pbs/scripts/update_endorsingrole_disclaimers.py
  python pbs/scripts/create_job_queue_groups.py
  
  ```



