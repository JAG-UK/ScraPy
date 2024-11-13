# Makefile

wheel:
	pip wheel . -w dist

format:
	black scrapi --line-length 79

lint:
	cd scrapi && pylint scrapi

