# ooy-docker-compose
Example Docker compose files for RapidPro and Casepro deployments for One 2 One Youth (LVCT)

The `migration` files will be used on the Praekelt.org VMs to deploy the instances that will be used for migrating the existing databases.
The other files will be used on the LVCT hosts to deploy the new production instances.

## External services required for CasePro:
* PostgreSQL database >= v9.6
* Redis host
* Email server

## External services required for RapidPro:
* PostgreSQL database >= v9.6
* Redis host
* ElasticSearch
* AWS S3 storage bucket
* Email server

Note: Casepro and RapidPro can connect to the same Redis host but should use different database ids

## Environment Variables
Most of the environment variables are populated by placeholders here because they contain secure credentials or because they are not yet known.
These will need to be replaced with the relevant values before the file can be used to start the containers.

When populating the values, look to the placeholder for clues on what the value should be. Some Variables have different names but the same placeholder. In these cases the same value is used.
All `url` placeholders expect the protocol to be included in the value (eg https://example.com). Some also expect the port (eg https://example.com:8000)
All `domain` placeholders are just the hostname (eg example.com)

### RapidPro environment variables
Some values should be in a specific format. These are detailed below:
* database_url_placeholder format: `postgresql://<username>:<password>@<host>/<database name>`
* redis_url_placeholder format: `redis://<host>:<port>/<redis database number>`
* elasitcsearch_url_placeholder format: `http://<host>:<port>`
* storage_url_placeholder format: `https://<bucket name>.s3.amazonaws.com`

### CasePro environment variables
Some values should be in a specific format. These are detailed below:
* database_url_placeholder format: `postgresql://<username>:<password>@<host>/<database name>`
* redis_host_placeholder format: `<host>:<port>`
* redis_db_placeholder format: `<redis database number>`
* rapidpro_contact_url_placeholder format: `<rapidpro_url_placeholder>/contact/read/%s/`

## How to run
Copy the compose file you wish to run and the nginx folder for the application to the server you wish to run it on. It should ideally be in a directory called "rapidpro" or "casepro".
Edit the file and replace any placeholders with the correct values for the environment variables.

### Production
(Note: The process for RapidPro and Casepro are the same. Just use the correct filename and replace any occurences of "rapidpro" in the instructions below with "casepro")
* It is advised to start the web container before the others. The web container will need extra time to spin up and apply any changes to the database schema.
* Start the web container with the command `docker-compose -f compose-rapidpro-565.yml -p rapidpro up -d rapidpro`
* Watch the logs and identify when the database schema changes have been completed, `docker-compose -f compose-rapidpro-565.yml -p rapidpro logs -f rapidpro`
* Start the rest of the containers with `docker-compose -f compose-rapidpro-565.yml -p rapidpro up -d`

### Local testing
The migration files can be used to run the applications locally, although not all features will work (search, email, ect)
(Note: The process for RapidPro and Casepro are the same. Just use the correct filename and replace any occurences of "rapidpro" in the instructions below with "casepro")
* Be sure to start the postgresql container first with `docker-compose -f compose-rapidpro-migration.yml -p rapidpro up -d postgresql`
* Once the postgresql container has spun up start the web container with `docker-compose -f compose-rapidpro-migration.yml -p rapidpro up -d rapidpro`
* Once the rapidpro container is finished applying any changes to the database the other containers can be started with `docker-compose -f compose-rapidpro-migration.yml -p rapidpro up -d`


