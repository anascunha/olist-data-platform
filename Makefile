.PHONY: setup up down shell download-data

setup:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

shell:
	docker-compose exec data_platform bash

download-data:
	docker-compose exec data_platform python pipelines/download_data.py
