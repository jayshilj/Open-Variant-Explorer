.PHONY: test run clean

test:
	python -m unittest discover -s tests -p "test_*.py" -v

run:
	streamlit run app.py

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
