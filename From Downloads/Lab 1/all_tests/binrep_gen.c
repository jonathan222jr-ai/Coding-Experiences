#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

// recursedigit(int n) function
void cse141recursedigit(int cse141n) {
    int cse141on;
    if (0 == cse141n) {
	return;
    }
    cse141on = 0;
    if (0 != (cse141n-((cse141n/2)*2))) {
        cse141on = 1;
    }
    cse141recursedigit(cse141n/2);
    if (0 == cse141on) {
	print("0");
    }
    if (1 == cse141on) {
	print("1");
    }
}

// the entry point
int main() {
    int cse141a;
    cse141a = 0;
    while (0 >= cse141a) {
	print("Give me a number: ");
	read(cse141a);
	
	if (0 >= cse141a) {
	    print("I need a positive integer.\n");
	}
    }
    print("The binary representation of: ");
    write(cse141a);
    print("is: ");
    cse141recursedigit(cse141a);
    print("\n\n");
}


