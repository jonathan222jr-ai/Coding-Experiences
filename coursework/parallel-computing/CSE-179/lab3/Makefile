CC = gcc
CFLAGS = -fopenmp -Wall -O2
TARGETS = linked prefix prod_cons

all: $(TARGETS)

linked: linked.c
	$(CC) $(CFLAGS) -o linked linked.c

prefix: prefix.c
	$(CC) $(CFLAGS) -o prefix prefix.c

prod_cons: prod_cons.c
	$(CC) $(CFLAGS) -o prod_cons prod_cons.c

clean:
	rm -f $(TARGETS)

.PHONY: all clean
