#include <stdio.h>
#define read(x) scanf("%d",&x)
#define write(x) printf("%d\n",x)
#define print(x) printf(x)

int cse141square(int cse141x)
{
    return (cse141x*cse141x+500)/1000;
}

int cse141complex_abs_squared(int cse141real, int cse141imag)
{
    return cse141square(cse141real)+cse141square(cse141imag);
}

int cse141check_for_bail(int cse141real, int cse141imag)
{
    if (cse141real > 4000 || cse141imag > 4000)
    {
	return 0;
    }
    if (1600 > cse141complex_abs_squared(cse141real, cse141imag))
    {
	return 0;
    }
    return 1;
}

int cse141absval(int cse141x)
{
    if (cse141x < 0)
    {
	return -1 * cse141x;
    }
    return cse141x;
}

int cse141checkpixel(int cse141x, int cse141y)
{
    int cse141real, cse141imag, cse141temp, cse141iter, cse141bail;
    cse141real = 0;
    cse141imag = 0;
    cse141iter = 0;
    cse141bail = 16000;
    while (cse141iter < 255)
    {
	cse141temp = cse141square(cse141real) - cse141square(cse141imag) + cse141x;
	cse141imag = ((2 * cse141real * cse141imag + 500) / 1000) + cse141y;
	cse141real = cse141temp;

	if (cse141absval(cse141real) + cse141absval(cse141imag) > 5000)
	{
	    return 0;
	}
	cse141iter = cse141iter + 1;
    }

    return 1;
}

int main() 
{
    int cse141x, cse141y, cse141on;
    cse141y = 950;

    while (cse141y > -950)
    {
	cse141x = -2100;
	while (cse141x < 1000)
	{
	    cse141on = cse141checkpixel(cse141x, cse141y);
	    if (1 == cse141on)
	    {
		print("X");
	    }
	    if (0 == cse141on)
	    {
		print(" ");
	    }
	    cse141x = cse141x + 40;
	}
	print("\n");

	cse141y = cse141y - 50;
    }
}

