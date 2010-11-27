clean:
	rm -rf `find . -type f -name "*.pyc"`
	rm -rf test
	
status: clean
	git status
	
rmtestdir:
	rm -rf test/cpp
	rm -rf test/sql
	
mktestdir: rmtestdir
	mkdir -p test/cpp
	mkdir -p test/sql
	
dbtest: mktestdir
	python3 src/main.py
	/Library/PostgreSQL/8.4/bin/psql -p 5433 -d test -f test/sql/crebas.sql
	wc -l test/sql/crebas.sql