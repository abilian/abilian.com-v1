.PHONY: all

all:
	./site build

push:
	rsync -e ssh -avz ./ dedi:abilian.com/
