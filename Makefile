lint:
	flake8 src

test:
	pytest --maxfail=1 --disable-warnings -q

format:
	black src
	isort src

build:
	python setup.py sdist bdist_wheel
