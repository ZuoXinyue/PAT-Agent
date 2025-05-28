using System;
using System.Collections.Generic;
using System.Text;
//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    /// <summary>
    /// The math library that can be used in your model.
    /// all methods should be declared as public static.
    /// 
    /// The parameters must be of type "int", or "int array"
    /// The number of parameters can be 0 or many
    /// 
    /// The return type can be bool, int or int[] only.
    /// 
    /// The method name will be used directly in your model.
    /// e.g. call(max, 10, 2), call(dominate, 3, 2), call(amax, [1,3,5]),
    /// 
    /// Note: method names are case sensetive
    /// </summary>
	public class extinction
	{
		static int TOPOLOGY = 0;
		const int TR = 10;
		
		static int N = 4;
		static int[] NC;
		static int[,] NCN;
		
		public static int init_extinction(int topo)
		{
			TOPOLOGY = topo;
			N = (topo == 1) ? 3 : 4;
			NC = new int[N];
			NCN = new int[N,3];
			
			for(int i = 0; i != N; ++i)
			{
				NC[i] = 0;
				for(int j = 0;  j != 3; ++j)
				{
					NCN[i,j] = 0;
				}
			}
			
			if(topo == 1)
			{
				NC[0] = 1; NCN[0,0] = 1;
				NC[1] = 2; NCN[1,0] = 0; NCN[1,1] = 2;
				NC[2] = 1; NCN[2,0] = 1;
			}
			else if(topo == 2)
			{
				NC[2] = 1; NCN[2,0] = 0;
				NC[0] = 2; NCN[0,0] = 2; NCN[0,1] = 3;
				NC[3] = 2; NCN[3,0] = 0; NCN[3,1] = 1;
				NC[1] = 1; NCN[1,0] = 3;
			}
			else
			{
				NC[0] = 2; NCN[0,0] = 1; NCN[0,1] = 2;
				NC[1] = 2; NCN[1,0] = 0; NCN[1,1] = 2;
				NC[2] = 3; NCN[2,0] = 1; NCN[2,1] = 0; NCN[2,2] = 3;
				NC[3] = 1; NCN[3,0] = 2;
			}
			
			return 0;
		}
		
		public static int get_N()
		{
			return N;
		}
		
		public static int get_NC(int x)
		{
			return NC[x];
		}
		
		public static int get_NCN(int x1, int x2)
		{
			return NCN[x1,x2];
		}
		
		public static int triple(int a, int b, int c)
		{
			return c + b * TR + a * TR * TR;
		}
		
		public static int third(int a)
		{
			return a % TR;
		}
		
		public static int second(int a)
		{
			return (a % (TR * TR))/TR;
		}
		
		public static int first(int a)
		{
			return a / (TR * TR);
		}
	}
}
