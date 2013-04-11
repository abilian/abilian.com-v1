.PHONY: all

run:
	./site serve

all:
	./site build

clean:
	rm -rf build
	find . -name "*.pyc" | xargs rm -f

push:
	rsync -e ssh -avz ./ dedi:abilian.com/
