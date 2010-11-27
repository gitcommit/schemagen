clean:
	rm -rf `find . -type f -name "*.pyc"`
	rm -rf test
status: clean
	git status
dbtest:
	mkdir -p test
	python3 src/main.py > test/crebas.sql
	/Library/PostgreSQL/8.4/bin/psql -p 5433 -d test -f test/crebas.sql
