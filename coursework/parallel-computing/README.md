# Parallel Computing (CSE-179)

Shared-memory, distributed-memory, and GPU parallelism labs in C/C++.

| Lab | Topic |
|---|---|
| `lab1` | Makefiles and build basics; profiling a serial program |
| `lab2` | OpenMP fundamentals — parallel loops, matrix–vector product |
| `lab3` | OpenMP linked lists, prefix sums, producer/consumer |
| `Lab4` | Pthreads — bank-account synchronization, a hand-rolled reader/writer lock, parallel π |
| `Lab5` | MPI point-to-point — ring communication |
| `Lab6` | MPI collectives, Cartesian topologies, and parallel I/O |
| `Lab8` | CUDA GPU assignment |
| `Lab9` | Parallel matrix multiply |
| `Lab10` | Parallel vs. serial Prim's minimum spanning tree, with a graph generator |

Each lab builds with `make` in its own directory.

## Note on scope

Lab 1's profiling exercise ran against **LULESH**, a hydrodynamics proxy application from
Lawrence Livermore National Laboratory. That benchmark is third-party code and is not
included here — only my own build and profiling work is published.
