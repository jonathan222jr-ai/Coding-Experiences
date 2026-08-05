#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141cse141square(int cse141cse141x)
{
    return (cse141cse141x*cse141cse141x+500)/1000;
}

int cse141cse141complex_abs_squared(int cse141cse141real, int cse141cse141imag)
{
    return cse141cse141square(cse141cse141real)+cse141cse141square(cse141cse141imag);
}

int cse141cse141check_for_bail(int cse141cse141real, int cse141cse141imag)
{
    if (cse141cse141real > 4000 || cse141cse141imag > 4000)
    {
	return 0;
    }
    if (1600 > cse141cse141complex_abs_squared(cse141cse141real, cse141cse141imag))
    {
	return 0;
    }
    return 1;
}

int cse141cse141absval(int cse141cse141x)
{
    if (cse141cse141x < 0)
    {
	return -1 * cse141cse141x;
    }
    return cse141cse141x;
}

int cse141cse141checkpixel(int cse141cse141x, int cse141cse141y)
{
    int cse141cse141real, cse141cse141imag, cse141cse141temp, cse141cse141iter, cse141cse141bail;
    cse141cse141real = 0;
    cse141cse141imag = 0;
    cse141cse141iter = 0;
    cse141cse141bail = 16000;
    while (cse141cse141iter < 255)
    {
	cse141cse141temp = cse141cse141square(cse141cse141real) - cse141cse141square(cse141cse141imag) + cse141cse141x;
	cse141cse141imag = ((2 * cse141cse141real * cse141cse141imag + 500) / 1000) + cse141cse141y;
	cse141cse141real = cse141cse141temp;

	if (cse141cse141absval(cse141cse141real) + cse141cse141absval(cse141cse141imag) > 5000)
	{
	    return 0;
	}
	cse141cse141iter = cse141cse141iter + 1;
    }

    return 1;
}

int main() 
{
    int cse141cse141x, cse141cse141y, cse141cse141on;
    cse141cse141y = 950;

    while (cse141cse141y > -950)
    {
	cse141cse141x = -2100;
	while (cse141cse141x < 1000)
	{
	    cse141cse141on = cse141cse141checkpixel(cse141cse141x, cse141cse141y);
	    if (1 == cse141cse141on)
	    {
		print("X");
	    }
	    if (0 == cse141cse141on)
	    {
		print(" ");
	    }
	    cse141cse141x = cse141cse141x + 40;
	}
	print("\n");

	cse141cse141y = cse141cse141y - 50;
    }
}

