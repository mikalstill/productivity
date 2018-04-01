.dockerbuilt: Dockerfile triptodos.py requirements.txt
	docker build -t triptodos .
	docker tag tripit_scraper localhost:5000/triptodos
	docker push localhost:5000/triptodos
	touch .dockerbuilt

build:	.dockerbuilt

run:	.dockerbuilt
	docker run triptodos
