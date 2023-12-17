test:
	python -m unittest

dist: test
	python -m build --sdist .

build_deps:
	python -m pip install build twine
