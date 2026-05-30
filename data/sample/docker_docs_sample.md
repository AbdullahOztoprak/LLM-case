# Docker Compose

Docker Compose is a tool for defining and running multi-container applications. A Compose
file describes the application's services, networks, and volumes.

## Start services

Run `docker compose up` in the directory with your Compose file to create and start the
defined services. Add `-d` to run containers in the background. Use `docker compose down`
to stop and remove the created containers and networks.

## Service configuration

Each service can define an image, build context, ports, volumes, and environment
variables.
