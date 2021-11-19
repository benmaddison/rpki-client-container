NAME=draft-ietf-sidrops-rpki-rsc
MOD=RpkiSignedChecklist-2021

OPENBSD_GIT=https://github.com/benmaddison/rpki-client-openbsd.git
OPENBSD_COMMIT=tree-limits

.PHONY: roas
roas: out/json
	cat $< | jq

out/json: .docker-image cache/ta/R/R.cer cache/rsync/rpki.example.net/rpki/R.cer tals/R.tal
	mkdir -p $(dir $@) && \
	IMAGE_NAME=$$(cat $<) && \
	docker run \
		--rm \
		--env ONESHOT="true" \
		--volume "$$(readlink -f $(dir $@)):/var/lib/rpki-client" \
		--volume "$(realpath cache):/var/cache/rpki-client" \
		--volume "$(realpath tals):/etc/tals" \
		$${IMAGE_NAME} -nvv

cache/ta/R/R.cer: cache/rsync/rpki.example.net/rpki/R.cer
	mkdir -p $$(dirname $@)
	cp $< $@

cache/rsync/rpki.example.net/rpki/R.cer tals/R.tal: .venv/bin/python3 gen-rpki-repos.py
	$< $(word 2,$^)

.venv/bin/python3: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -r $<
	.venv/bin/python3 --version

.docker-image: Dockerfile rpki-client.pub entrypoint.sh healthcheck.sh
	IMAGE_NAME=rpki-client-tree-limits-$$(cat $^ | sha512sum | head -c 8) && \
	docker build \
		--build-arg OPENBSD_GIT=$(OPENBSD_GIT) \
		--build-arg OPENBSD_COMMIT=$(OPENBSD_COMMIT) \
		--tag $${IMAGE_NAME} \
		. && \
	echo -n $${IMAGE_NAME} > $@

.PHONY: clean
clean: clean-image clean-venv
	rm -rf out/ cache/ tals/

.PHONY: clean-image
clean-image: .docker-image
	IMAGE_NAME=$$(cat $<) && \
	docker image rm $${IMAGE_NAME} && \
	rm $<

.PHONY: clean-venv
clean-venv:
	rm -rf .venv
