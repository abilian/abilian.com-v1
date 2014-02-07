.PHONY: all

run:
	./main.py serve

all:
	./main.py build

clean:
	rm -rf build
	rm -rf ./static/.webassets-cache
	find . -name "*.pyc" | xargs rm -f
	find . -name packed.js | xargs rm -f
	find . -name packed.css | xargs rm -f

deploy:
	  ansible-playbook -i deployment/hosts deployment/server.yml

push:
	rsync -e ssh -avz ./ dedi:/srv/abilian.com/

