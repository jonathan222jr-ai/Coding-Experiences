#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141g()
{
    return 1;
}

int cse141f()
{
    return cse141g() + 1;
}

int cse141e()
{
    return cse141f() + 1;
}

int cse141d()
{
    return cse141e() + 1;
}

int cse141c()
{
    return cse141d() + 1;
}

int cse141b()
{
    return cse141c() + 1;
}

int cse141a()
{
    return cse141b() + 1;
}

int main() 
{
    int cse141val;
    cse141val = cse141a();

    print("I calculate the answer to be: ");
    write(cse141val);
}
