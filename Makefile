all:
	python oracle.py

clean:
	rm -rf corpora/*.txt
	rm -rf models/*.pkl
