CC = mpicc
CFLAGS = -Wall -Wextra -O2

all: hello ring

hello: MPI_simple.c
	$(CC) $(CFLAGS) MPI_simple.c -o hello

ring: MPI_ring.c
	$(CC) $(CFLAGS) MPI_ring.c -o ring

run-hello:
	mpirun -np 4 ./hello

run-ring:
	mpirun -np 4 ./ring

clean:
	rm -f hello ring