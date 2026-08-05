#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141cse141cse141array[16];

void cse141cse141cse141initialize_array(void)
{
    int cse141cse141cse141idx, cse141cse141cse141bound;
    cse141cse141cse141bound = 16;

    cse141cse141cse141idx = 0;
    while (cse141cse141cse141idx < cse141cse141cse141bound)
    {
	cse141cse141cse141array[cse141cse141cse141idx] = -1;
	cse141cse141cse141idx = cse141cse141cse141idx + 1;
    }
}

int cse141cse141cse141fib(int cse141cse141cse141val)
{
    if (cse141cse141cse141val < 2)
    {
	return 1;
    }
    if (cse141cse141cse141array[cse141cse141cse141val] == -1)
    {
	cse141cse141cse141array[cse141cse141cse141val] = cse141cse141cse141fib(cse141cse141cse141val - 1) + cse141cse141cse141fib(cse141cse141cse141val - 2);
    }

    return cse141cse141cse141array[cse141cse141cse141val];
}

int main(void)
{
    int cse141cse141cse141idx, cse141cse141cse141bound;
    cse141cse141cse141bound = 16;

    cse141cse141cse141initialize_array();
    
    cse141cse141cse141idx = 0;

    print("The first few digits of the Fibonacci sequence are:\n");
    while (cse141cse141cse141idx < cse141cse141cse141bound)
    {
	write(cse141cse141cse141fib(cse141cse141cse141idx));
	cse141cse141cse141idx = cse141cse141cse141idx + 1;
    }
}
