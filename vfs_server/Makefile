.PHONY: compile test qualify
compile:
	python -m compileall -q vfs_server
test:
	python -m unittest discover -s vfs_server/tests -v
qualify:
	python -m vfs_server.qualification
