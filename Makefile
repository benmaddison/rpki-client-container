.PHONY: roas
roas: out/json
	cat $< | jq

out/json: tals/R.tal build
	mkdir -p $(dir $@)
	docker-compose run rpki-client
	docker-compose down

tals/R.tal: .venv/bin/python3 gen-rpki-repos.py
	$< $(word 2,$^)

.venv/bin/python3: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -r $<
	.venv/bin/python3 --version

.PHONY: build
build: docker-compose.yml
	docker-compose build

.PHONY: clean
clean:
	rm -rf out/ cache/ tals/ .venv/
