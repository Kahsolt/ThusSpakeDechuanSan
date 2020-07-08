all:
	python oracle.py

clean:
	rm -rf corpus/*.txt
	rm -rf models/*.pkl
