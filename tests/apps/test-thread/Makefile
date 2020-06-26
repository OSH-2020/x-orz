.PHONY: module
module: test

CFLAGS = -std=gnu99 -fpie -rdynamic -pthread

test: test.c
	$(CC) -pie -o $@ $(CFLAGS) $(LDFLAGS) test.c

clean:
	rm -f test
