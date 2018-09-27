.dockerbuilt: Dockerfile triptodos.py requirements.txt
	docker login harbor.home.stillhq.com
	docker build -t triptodos .
	docker tag tripit_scraper harbor.home.stillhq.com/stillhq/triptodos
	docker push harbor.home.stillhq.com/stillhq/triptodos
	touch .dockerbuilt

build:	.dockerbuilt

run:	.dockerbuilt
	docker run triptodos
