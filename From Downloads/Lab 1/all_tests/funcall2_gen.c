#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141c()
{
    return 1;
}

int cse141b()
{
    return 2;
}

int cse141a()
{
    return 3;
}

int cse141foo(int cse141a, int cse141b, int cse141c)
{
    return (cse141a*3 + cse141b*2 + cse141c);
}

int main() 
{
    int cse141val;
    cse141val = cse141foo(cse141a(), cse141b(), cse141c());

    print("I calculate the answer to be: ");
    write(cse141val);
}
