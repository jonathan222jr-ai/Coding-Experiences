#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141cse141array_1[4];
int cse141cse141array_2[4];

void cse141cse141populate_arrays(void)
{
    cse141cse141array_1[0] = 0;
    cse141cse141array_1[1] = 1;
    cse141cse141array_1[2] = 1;
    cse141cse141array_1[3] = 2;

    cse141cse141array_2[0] = 3;
    cse141cse141array_2[1] = 5;
    cse141cse141array_2[2] = 8;
    cse141cse141array_2[3] = 13;
}

int main(void)
{
    int cse141cse141idx, cse141cse141bound;

    cse141cse141populate_arrays();
    
    cse141cse141idx = 0;
    cse141cse141bound = 8;

    print("The first few digits of the Fibonacci sequence are:\n");
    while (cse141cse141idx < cse141cse141bound)
    {
	write(cse141cse141array_1[cse141cse141idx]);
	cse141cse141idx = cse141cse141idx + 1;
    }
}
