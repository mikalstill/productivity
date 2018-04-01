.dockerbuilt: Dockerfile tripit_scraper.py requirements.txt
	docker build -t tripit_scraper .
	docker tag tripit_scraper localhost:5000/tripit_scraper
	docker push localhost:5000/tripit_scraper
	touch .dockerbuilt

build:	.dockerbuilt

run:	.dockerbuilt
	docker run tripit_scraper
