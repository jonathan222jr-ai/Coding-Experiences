SRC = $(wildcard src/*.c)
OBJ = $(patsubst src/%.c,obj/%.o,$(SRC))
CC = gcc

obj/printfunc.o: src/printfunc.c
	mkdir -p obj
	gcc -c $< -o $@


learn_makefile: $(OBJ)
	gcc -o $@ $^


all: learn_makefile


.PHONY: clean
clean:
	rm -rf obj learn_makefile
