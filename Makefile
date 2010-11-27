first: fulltest

clean:
	rm -rf `find . -type f -name "*.pyc"`
	rm -rf test
	
status: clean
	git status
	
rmcpptestdir:
	rm -rf test/cpp
	
rmsqltestdir:
	rm -rf test/sql
	
mkcpptestdir: rmcpptestdir
	mkdir -p test/cpp
	
mksqltestdir: rmsqltestdir
	mkdir -p test/sql
	
dbtest: mksqltestdir
	python3 src/main.py crebas
	/Library/PostgreSQL/8.4/bin/psql -p 5433 -d test -f test/sql/crebas.sql
	wc -l test/sql/crebas.sql
	
cpptest: mkcpptestdir
	python3 src/main.py cpp
	
fulltest: cpptest dbtest