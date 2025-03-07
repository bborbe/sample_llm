
run: index search

index:
	python index.py

search:
	python search.py

qdrant:
	docker kill qdrant || true
	docker run \
	--rm \
	--name qdrant \
	-p 6333:6333 \
	qdrant/qdrant
