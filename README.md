# ooy-docker-compose
Docker-compose file  (named compose-combined.yaml) for the deployments of RapidPro (and additional components), Casepro, Content Repository and Big Query sync script for One 2 One Youth (LVCT). The docker-compose file also runs an Nginx container to direct traffic to the various applications.

The files are used on the LVCT hosts to deploy the production instances.

All services are configured to send error reports to Sentry  (excl. ElasticSearch and Nginx).

Python script to run as an AGI command in the Asterisk dialplan and make calls to RapidPro's API

## Environment Variables
Most configuration settings for the applications are provided through environment variables in the Docker compose file named compose-combined.yaml. Any sensitive variables have been redacted in this repository but any that are safe for public view are listed.

## RapidPro
RapidPro is a Django application that allows anyone to build interactive messaging systems over multiple different channels http://rapidpro.github.io/rapidpro/

### RapidPro Components
RapidPro requires additional applications to be running in order to process messages and flows.
The detail for these can be found in the RapidPro documentation http://rapidpro.github.io/rapidpro/docs
The additional applications running for LVCT are:
* Courier (http://rapidpro.github.io/rapidpro/docs/courier/)
* Mailroom (http://rapidpro.github.io/rapidpro/docs/mailroom/)
* Indexer (http://rapidpro.github.io/rapidpro/docs/indexer/)

### External services required for RapidPro:
* PostgreSQL database >= v9.6
* Redis host
* ElasticSearch
* AWS S3 storage bucket
* Email server

## Casepro
Casepro is a Case management dashboard built on Django that allows operators to manage and respond to messages from customers (https://github.com/rapidpro/casepro/wiki)
Note: Casepro is configured with a wildcard domain because it creates a new subdomain for each organisation configured.
### External services required for CasePro:
* PostgreSQL database >= v9.6
* Redis host
* Email server

## Content Repository
The Content Repository is a Wagtail project developed by Praekelt.org to improve the content management experience for maintainers of messaging systems.
### External services required for Content Repository:
* PostgreSQL database >= v9.6
* Redis host

## Big Query sync script
The Big Query sync script is a small Python application that pulls data from the RapidPro API and pushes it to Google Big Query for analysis and reporting
### External services required for Big Query sync script:
* Google Big Query account

## Nginx
An Nginx webserver is set up in the docker-compose file, it uses the included nginx.conf file for it's configuration. It's purpose is to route traffic to the correct containers based on the requested url. It will also serve media and static files directly from the containers.

### Setup Notes
Ports 80 and 443 needed to be exposed on the host server and firewall to allow requests through.

## ElasticSearch
An ElasticSearch container required to make use of RapidPro's search features.

### Setup Notes
In order to run ElasticSearch in a Docker container the `vm.max_map_count` on the host server had to be modified. Details of this can be found here https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#_set_vm_max_map_count_to_at_least_262144

## PostgreSQL
A PostgreSQL v10.19 server is running on the host machine containing the databases for RapidPro, Casepro and Content Repository.

### Setup Notes
The firewall should block external access to the port used by PostgreSQL
In order to allow containers on the host machine to connect to the database server some changes had to be made to the configuration of PostgreSQL.
* Allow connections from the Docker network by adding `host  all  all  172.16.0.0/12  md5` to `/etc/postgresql/10/main/pg_hba.conf`
* Added `listen_addresses = '10.0.10.4'` to `/etc/postgresql/10/main/postgresql.conf`
* The database extensions required by the Casepro and RapidPro databases had to be added to each database manually (restoring the database from a dump did not add them)

## Redis
Many of the applications use a Redis server on the host machine for caching and/or as their broker for Celery.
Note: Separate applications can connect to the same Redis host but should use different database ids.

### Setup Notes
A configuration change was required in order for the Docker containers to be able to connect to the Redis server. `bind 0.0.0.0` was added to `/etc/redis/redis.conf`.
The firewall should block external access to the port being used by Redis

## Running applications
Any application (or "service" in docker-compose terminology) listed in the compose file can be run using the service name:
`sudo docker-compose -f combined/compose-combined.yml up -d <service name>`
for example, the command below would run the Celery container for the Casepro installation and then detach from it:
`sudo docker-compose -f combined/compose-combined.yml up -d casepro-celery`
Note that some applications are configured to be dependent on other services, starting these applications will also start the applications they are dependant on.

## Logs
Logs for a service can be viewed with
`sudo docker-compose -f combined/compose-combined.yml logs -f <service name>`
*Note*: limitations on the server storage space have required restrictions to be placed on the log sizes. Only one log file is allowed per container and log files can be a maximum of 500mb. Once a file reaches that limit it is "rotated". This means all previous data in the logs is lost.

## Stop containers
Application containers can be stopped with
`sudo docker-compose -f combined/compose-combined.yml stop <service name>`


## Known issues
### Casepro stops syncing messages
Sometimes the Casepro Celery workers will get stuck and stop pulling messages and data from RapidPro.
*Identification*: If both Casepro and RapidPro are accessible in the browser and messages are appearing in RapidPro but no messages are appearing in Casepro then this is likely the cause.
*Fix*: If this issue occurs again the solution is to restart the Casepro Celery container with the following command
`sudo docker-compose -f combined/compose-combined.yml restart casepro-celery`
*Mitigation (implemented)*: Casepro Celery has been configured to start with `"--concurrency=2", "--time-limit=30", "--max-tasks-per-child=100"`. The issue has not occurred since these settings have been put in place.

### Server disk full
The disk capacity of the server is very low for the systems running there. There have been a few instances where Docker logs have caused the disk to fill up completely. This is a significant concern since the database is housed on the same disk and data could become corrupted or lost while the disk is full.
*Identification*: Nothing on the server will be working correctly. RapidPro and Casepro do not load in the browser. Connecting to the server via ssh will show `Usage of /: 100% of 28.90GB` in the welcome message.
*Fix*: Identify what is taking up significant disk space that shouldn't be and remove it.
The disk usage of docker logs can be seen with the following command
`sudo sh -c "du -ch /var/lib/docker/containers/*/*-json.log"`
Unused docker objects can be removed with
`sudo docker system prune`
Once disk space has been made available it might be necessary to restart the server to ensure database connections are correctly restored.
*Mitigation (implemented)*: Docker logs are restricted to 500mb per container.
*Mitigation (recommended)*: Move the database to a dedicated server. And/Or move Docker onto a seperate file system and use a symlink on the existing filesystem to connect them.

### RapidPro stops sending messages
RapidPro was built to be run as a platform service and as such there are automated systems put in place to prevent abuse. An unidentified aspect of the current system sometimes causes these systems to trigger and the LVCT Workspace on RapidPro gets flagged for sending Spam.
*Identification*: No outbound messages will be sent. When trying to manually send a message from RapidPro the UI will show the error "Sorry, your workspace is currently flagged. To enable sending messages please contact support."
*Fix*: In order to fix this a developer must run a shell in the container and reset the flag on the workspace. This can be done using the sequence of commands below.
`sudo docker exec -it combined_rapidpro_1 /bin/ash` Runs an interactive ash session in the container
`source ../venv/bin/activate` Activates the virtual environment the application is running in
`./manage.py shell` Starts a Django shell with the settings used by the application
Run the python code below in the shell to resolve the issue
`from temba.orgs.models import Org`
`org = Org.objects.filter(slug="lvcthealth")`
`org.is_flagged = False`
`org.save()`
*Mitigation*: There is currently no known mitigation for this issue.

### Applications do not start up on docker restart
If Docker or the whole server need to be restarted all the Docker containers will stop running and will not automatically restart. They must be restarted manually.
*Identification*: `sudo docker ps` shows no containers running
*Fix*: Start up all the services (It is recommended to use the order below)
`sudo docker-compose -f combined/compose-combined.yml start elasticsearch contentrepo casepro casepro-celery mailroom courier rapidpro`
`sudo docker-compose -f combined/compose-combined.yml start bigquery-sync indexer rapidpro-celery rapidpro-beat nginx`
*Mitigation (recommended)*: Configure the services in the docker-compose file to start on server startup

## Upgrades
### RapidPro
When upgrading RapidPro please take into account their versioning practices and upgrade recommendations https://github.com/rapidpro/rapidpro#versioning-in-rapidpro. Always upgrade to a stable release.

LVCT is running RapidPro using Praekelt.org's Docker images. So confirm that the version you wish to update to for each component has been built and pushed to Docker Hub (or GitHub Container Repository in future)
We are currently working on the 7.0 release upgrade which has some significant changes to the Docker build process
#### Docker Hub repositories
* Rapidpro - https://hub.docker.com/r/praekeltfoundation/rapidpro/tags
* Mailroom - https://hub.docker.com/r/praekeltfoundation/mailroom/tags
* Courier - https://hub.docker.com/r/praekeltfoundation/courier/tags
* Indexer - https://hub.docker.com/r/praekeltfoundation/rp-indexer/tags
#### Dockerfiles
* Rapidpro - https://github.com/praekeltfoundation/rapidpro-docker
* Mailroom - https://github.com/praekeltfoundation/mailroom-docker
* Courier - https://github.com/praekeltfoundation/courier-docker
* Indexer - https://github.com/praekeltfoundation/rp-indexer-docker

#### Notes
* Always compare the settings file for the new version to the settings file for your current version. Take note of any environment variables that need to be added or that may have changed.
* Always review the ChangeLog entries for the versions you will be progressing through and address any infrastructure upgrades that might be necessary (https://github.com/rapidpro/rapidpro/blob/main/CHANGELOG.md)
* Always take a backup of the database and test the upgrade process in a test environment first.
* Identify the version number for each component that makes up the stable release you are moving to https://github.com/rapidpro/rapidpro#stable-versions

#### Process
1. Stop the rapidpro, rapidpro-celery, rapidpro-beat, mailroom, courier and indexer containers with
`sudo docker-compose -f combined/compose-combined.yml stop rapidpro rapidpro-celery rapidpro-beat mailroom courier indexer`
2. Change the image tag used by the mailroom service in the compose file to use the new version
3. Edit the docker-compose file (compose-combined) and change the startup command for mailroom to ensure it starts up without any workers
`["mailroom", "--address", "0.0.0.0", "-batch-workers", "0", "-handler-workers", "0"]`
4. Start mailroom service with
`sudo docker-compose -f combined/compose-combined.yml up -d mailroom`
5. Change the image tag used by the rapidpro service in the compose file to use the new version and make any necessary changes to environment variables
6. Start the rapidpro service in order to run the database migrations
`sudo docker-compose -f combined/compose-combined.yml up -d rapidpro`
7. Tail the logs to confirm that the migrations have completed successfully
`sudo docker-compose -f combined/compose-combined.yml logs -f rapidpro`
8. Stop mailroom
`sudo docker-compose -f combined/compose-combined.yml stop mailroom`
9. Edit the docker-compose file again to set the mailroom startup command back to what it was
`["mailroom", "--address", "0.0.0.0"]`
10. Restart mailroom
`sudo docker-compose -f combined/compose-combined.yml up -d mailroom`
11. Change the image tag used by the courier service in the compose file to use the new version
12. Change the image tag used by the indexer service in the compose file to use the new version
13. Change the image tag used by the rapidpro-celery and rapidpro-beat services in the compose file to use the new version and make any necessary changes to environment variables
14. Start up the extra services again
`sudo docker-compose -f combined/compose-combined.yml up -d courier indexer rapidpro-celery rapidpro-beat`
14. You may need to restart the nginx service if RapidPro doesn't load in a browser
`sudo docker-compose -f combined/compose-combined.yml restart nginx`

### Casepro
LVCT is running Casepro using Praekelt.org's Docker images. So confirm that the version you wish to update to has been built and pushed to Docker Hub (or GitHub Container Repository in future)
https://hub.docker.com/r/praekeltfoundation/casepro-docker

#### Notes
* Always compare the settings file for the new version to the settings file for your current version. Take note of any environment variables that need to be added or that may have changed.
* Always review the ChangeLog entries for the versions you will be progressing through and address any infrastructure upgrades that might be necessary (https://github.com/rapidpro/casepro/blob/main/CHANGELOG.md)
* Always take a backup of the database and test the upgrade process in a test environment first.

#### Process
1. Stop the casepro and casepro-celery containers with
`sudo docker-compose -f combined/compose-combined.yml stop casepro casepro-celery`
2. Change the image tag used by the casepro service in the compose file to use the new version and make any necessary changes to environment variables
3. Start the casepro service in order to run the database migrations
`sudo docker-compose -f combined/compose-combined.yml up -d casepro`
4. Tail the logs to confirm that the migrations have completed successfully
`sudo docker-compose -f combined/compose-combined.yml logs -f casepro`
5. Change the image tag used by the casepro-celery service in the compose file to use the new version and make any necessary changes to environment variables
6. Start up the celery again
`sudo docker-compose -f combined/compose-combined.yml up -d courier indexer casepro-celery`
7. You may need to restart the nginx service if Casepro doesn't load in a browser
`sudo docker-compose -f combined/compose-combined.yml restart nginx`

### Content Repo
The Content Repo application is built and maintained by Praekelt.org. So confirm that the release you wish to update to has been built and is available in GitHub Container Repository

#### Notes
* Always compare the settings file for the new version to the settings file for your current version. Take note of any environment variables that need to be added or that may have changed.
* Always take a backup of the database and test the upgrade process in a test environment first.

#### Process
1. Stop the contentrepo container with
`sudo docker-compose -f combined/compose-combined.yml stop contentrepo`
2. Change the image tag used by the contentrepo service in the compose file to use the new version and make any necessary changes to environment variables
3. Start the contentrepo service in order to run the database migrations
`sudo docker-compose -f combined/compose-combined.yml up -d contentrepo`
4. Tail the logs to confirm that the migrations have completed successfully
`sudo docker-compose -f combined/compose-combined.yml logs -f contentrepo`
5. You may need to restart the nginx service if Casepro doesn't load in a browser
`sudo docker-compose -f combined/compose-combined.yml restart nginx`


## AGI Script
The Asterisk Integration script enables rudimentary integration between a call center running on an Asterisk PBX and a RapidPro instance. The script accepts details about a  call that has been concluded, creates the Contact in RapidPro (via the API) and starts them on a flow to store the details on their contact profile. These details can then be surfaced in later interactions with the call center operators or used for reporting.

### Setup
In order to install dependency libraries and keep them isolated from the rest of the system the script is setup to run in a virtual environment.

The following steps were followed to set this up
1. Install pip
`curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py`
`sudo python get-pip.py`
2. Create a folder to house everything related to the script (/opt/ is the dir where AGI scripts are loaded from)
`sudo mkdir /opt/rapidpro_connection`
3. Navigate into the folder
`cd /opt/rapidpro_connection`
4. Copy the script and requirements.txt to the directory
5. Install virtualenv to create the environment
`sudo python -m pip install virtualenv`
6. Create and activate the virtual environment
`sudo virtualenv -p python3.8 venv`
`source venv/bin/activate`
7. Install dependency libraries in the virtual environment
`sudo /opt/rapidpro_connection/venv/bin/pip install -r requirements.txt`
8. Set execute permissions on the script
`chmod 777 send_to_rapidpro.py`
9. Create a .env file containing the required environment variables (see example.env)

### Integration
Calling the script from Asterisk requires a few lines to be added to the dailplan.
Firstly some lines are added to store the Msisdn, call start time and call direction as variables in the dialplan. We also register the \[rapidpro\] context as a hangup handler for the call.
These lines are added to the \[covid19\] context for inbound calls
```
exten => s,n,Set(CALL_START=${STRFTIME(${EPOCH},,%Y-%m-%dT%H:%M:%S)})
exten => s,n,Set(MSISDN=${CALLERID(num)})
exten => s,n,Set(CALL_DIRECTION="inbound")
exten => s,n,Set(CHANNEL(hangup_handler_push)=rapidpro,s,1(${CALL_START},${MSISDN},${CALL_DIRECTION}));
```
While these lines are added to the \[lvctsip\] context for outbound calls
```
exten => _0XXXXXXXXX,n,Set(CALL_START=${STRFTIME(${EPOCH},,%Y-%m-%dT%H:%M:%S)})
exten => _0XXXXXXXXX,n,Set(MSISDN=${EXTEN})
exten => _0XXXXXXXXX,n,Set(CALL_DIRECTION="outbound")
exten => _0XXXXXXXXX,n,Set(CHANNEL(hangup_handler_push)=rapidpro,s,1(${CALL_START},${MSISDN},${CALL_DIRECTION}));
```
The \[rapidpro\] context is then where the script is actually called with the collected variables as arguments sent via stdin
```
[rapidpro]
exten => s,1,Set(CALL_END=${STRFTIME(${EPOCH},,%Y-%m-%dT%H:%M:%S)})
exten => s,2,AGI(/opt/rapidpro_connection/update_user_rapidpro.py,"${MSISDN}",${CALL_START},${CALL_END},"${CALL_DIRECTION}")
same => n,Return()
```