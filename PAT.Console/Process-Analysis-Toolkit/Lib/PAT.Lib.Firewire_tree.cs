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
    public class firewire_tree
    {    	
    	public static int adj(int[] connected, int x, int N)
    	{
    		int tmp = 0;
    		for(int y = 0; y != N; ++y)
    		{
    			tmp += connected[x * N + y];
    		}
    		return tmp;
    	}
    	
    	public static int add_array(int[] arr, int length)
    	{
    		int tmp = 0;
    		for(int i = 0; i != length; ++i)
    		{
    			tmp += arr[i];
    		}
    		return tmp;
    	}
    	    	
    	public static int all_not_received(int[] received, int id, int N)
    	{
    		for(int i = 0; i != N; ++i)
    		{
    			if(received[id * N + i] == 1)
    			{
    				return 0;
    			}
    		}
    		
    		return 1;
    	}
    }
}
