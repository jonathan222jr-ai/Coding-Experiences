CC = gcc
CFLAGS = -Wall -pthread

# Programs
TARGET1 = test03_my
TARGET2 = bankAccount
TARGET3 = pi_pthreads

# Object files
OBJ1 = test03_my.o my_rwlock.o
OBJ2 = bankAccount.o
OBJ3 = pi_pthreads.o

all: $(TARGET1) $(TARGET2) $(TARGET3)

# ----- Read/Write Lock Program -----
$(TARGET1): $(OBJ1)
	$(CC) $(CFLAGS) -o $(TARGET1) $(OBJ1)

test03_my.o: test03_my.c my_rwlock.h check.h
	$(CC) $(CFLAGS) -c test03_my.c

my_rwlock.o: my_rwlock.c my_rwlock.h
	$(CC) $(CFLAGS) -c my_rwlock.c


# ----- Bank Account Program -----
$(TARGET2): $(OBJ2)
	$(CC) $(CFLAGS) -o $(TARGET2) $(OBJ2)

bankAccount.o: bankAccount.c bankAccount.h
	$(CC) $(CFLAGS) -c bankAccount.c


# ----- PI pthread Program -----
$(TARGET3): $(OBJ3)
	$(CC) $(CFLAGS) -o $(TARGET3) $(OBJ3)

pi_pthreads.o: pi_pthreads.c
	$(CC) $(CFLAGS) -c pi_pthreads.c


# ----- Clean -----
clean:
	rm -f *.o $(TARGET1) $(TARGET2) $(TARGET3)