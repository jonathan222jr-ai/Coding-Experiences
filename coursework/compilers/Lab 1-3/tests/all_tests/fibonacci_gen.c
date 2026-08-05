#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141array[16];

void cse141initialize_array(void)
{
    int cse141idx, cse141bound;
    cse141bound = 16;

    cse141idx = 0;
    while (cse141idx < cse141bound)
    {
	cse141array[cse141idx] = -1;
	cse141idx = cse141idx + 1;
    }
}

int cse141fib(int cse141val)
{
    if (cse141val < 2)
    {
	return 1;
    }
    if (cse141array[cse141val] == -1)
    {
	cse141array[cse141val] = cse141fib(cse141val - 1) + cse141fib(cse141val - 2);
    }

    return cse141array[cse141val];
}

int main(void)
{
    int cse141idx, cse141bound;
    cse141bound = 16;

    cse141initialize_array();
    
    cse141idx = 0;

    print("The first few digits of the Fibonacci sequence are:\n");
    while (cse141idx < cse141bound)
    {
	write(cse141fib(cse141idx));
	cse141idx = cse141idx + 1;
    }
}
