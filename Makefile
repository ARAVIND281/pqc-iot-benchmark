.PHONY: setup benchmark analyze paper clean

setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

benchmark:
	python3 run_pipeline.py --stages benchmark

analyze:
	python3 run_pipeline.py --stages analyze,figures

paper:
	cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

clean:
	rm -rf analysis/__pycache__ src/__pycache__ tests/__pycache__
	rm -f paper/*.aux paper/*.log paper/*.out paper/*.bbl paper/*.blg paper/*.fls paper/*.fdb_latexmk paper/*.synctex.gz
