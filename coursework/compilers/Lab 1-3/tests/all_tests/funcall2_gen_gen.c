#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141cse141c()
{
    return 1;
}

int cse141cse141b()
{
    return 2;
}

int cse141cse141a()
{
    return 3;
}

int cse141cse141foo(int cse141cse141a, int cse141cse141b, int cse141cse141c)
{
    return (cse141cse141a*3 + cse141cse141b*2 + cse141cse141c);
}

int main() 
{
    int cse141cse141val;
    cse141cse141val = cse141cse141foo(cse141cse141a(), cse141cse141b(), cse141cse141c());

    print("I calculate the answer to be: ");
    write(cse141cse141val);
}
