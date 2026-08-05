#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

void cse141bar(void)
{
    int cse141x, cse141y;
    if (cse141x > cse141y)
    {
	return;
    }

    cse141x = cse141y;
    return;
}

void cse141foo(void)
{
    cse141bar();
}

int main(void)
{
    int cse141x,cse141y;
    print("Calling foo()...\n");
    cse141foo();
    print("Called foo().\n");

    cse141x == cse141y;
}
