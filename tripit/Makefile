.dockerbuilt: Dockerfile tripit_scraper.py tripit.py requirements.txt
	docker login harbor.home.stillhq.com
	docker build -t tripit_scraper .
	docker tag tripit_scraper harbor.home.stillhq.com/stillhq/tripit_scraper
	docker push harbor.home.stillhq.com/stillhq/tripit_scraper
	touch .dockerbuilt

build:	.dockerbuilt

run:	.dockerbuilt
	docker run tripit_scraper
