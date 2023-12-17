.PHONY: test
test:
	PYTHONPATH=src python -m unittest

dist: test
	python -m build --sdist .

build_deps:
	python -m pip install build
	python -m pip install twine

.PHONY: deploy_check
deploy_check:
	twine check dist/*

.PHONY: deploy_test
deploy_test: deploy_check
	# https://test.pypi.org/project/gcode-machine
	# python3 -m pip install --index-url https://test.pypi.org/simple/ gcode-machine
	twine upload --repository testpypi --sign dist/*

.PHONY: deploy_PRODUCTION
deploy_PRODUCTION: deploy_check
	# https://pypi.org/project/gcode-machine
	# python3 -m pip install gcode-machine
	twine upload --sign dist/*
