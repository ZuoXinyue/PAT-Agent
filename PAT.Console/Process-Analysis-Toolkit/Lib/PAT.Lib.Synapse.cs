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
    public class synapse
    {
		public static int cal_valid_value(int value, int m)
		{
			return ((value & (1 << m))/(1 << m));
		}
		
		public static int cal_set_value(int value, int first_m, int second_m)
		{
			return value - (value & (1<<(first_m))) + (second_m * (1<<(first_m)));
		}
    }
}
