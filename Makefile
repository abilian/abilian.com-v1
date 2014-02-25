.PHONY: run clean deploy push

SRC=website

run:
	./run.py serve

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


update-pot:
	# _n => ngettext, _l => lazy_gettext
	pybabel extract -F etc/babel.cfg -k "_n:1,2" -k "_l"\
	    -o $(SRC)/i18n/messages.pot "${SRC}"
	pybabel update -i $(SRC)/i18n/messages.pot \
	    -d $(SRC)/i18n
	pybabel compile -d $(SRC)/i18n
