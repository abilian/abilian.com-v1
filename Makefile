.PHONY: all

run:
	./main.py serve

all:
	./main.py build

clean:
	rm -rf build
	find . -name "*.pyc" | xargs rm -f

push:
	rsync -e ssh -avz ./ dedi:abilian.com/
