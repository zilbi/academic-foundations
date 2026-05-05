fmt:
	ruff check --select I --fix .
	ruff format . --no-cache
	@echo '[OK] Formatters went through successfully'

lint:
	ruff check solution --no-cache
	@echo '[OK] Linters checks passed successfully'

run:
	uvicorn solution.main:app --reload

test:
	pytest test -s

test-perf:
	pytest test/test_performance.py -s
