CC = gcc
CFLAGS = -Wall -O2 -fopenmp
TARGETS = openmp_simple openmp_matvec

.PHONY: all clean
all: $(TARGETS)

openmp_simple: openmp_simple.c
	$(CC) $(CFLAGS) -o $@ $<

openmp_matvec: openmp_matvec.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGETS)