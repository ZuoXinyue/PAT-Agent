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
    public class Prob
    {
	       public static int probability(int[] ActionHolder, int i, int j)
        {
		       if(ActionHolder[i] == 1)
		          return 0;
		         else 
		         return 1;
        }
        public static int probability_1(int[] ActionHolder, int i, int j, int num_of_agent, int num_of_action)
        {
        	int num = 0;
        	for(int k = 1; k <= num_of_action; k ++)
        	{
        		if(ActionHolder[k] < numOfPlayerceiling(num_of_agent,num_of_action))
        		{
        			num++;
        		}
        	}
        	double prob1 =  ((double)num_of_agent)/num_of_action/ActionHolder[j];
        	double prob2 = (1 - prob1)/num;
       
        	if(i == j)
        	{
        		return (int)(prob1 * 100);
        	}
        	else if(ActionHolder[i] < numOfPlayerceiling(num_of_agent,num_of_action))
        	{
        		return (int)(prob2 * 100);
        	}	
        	else
        	{
        		return 0;
        	}
        
        }
        public static int numOfPlayerceiling(int num_of_agent, int num_of_action)
        {
        	if(num_of_agent%num_of_action == 0)
        	{
        		return  num_of_agent/num_of_action;
        	}
        	else
        	{
        		return  num_of_agent/num_of_action + 1;
        	}
        }
         public static int numOfPlayerfloor(int num_of_agent, int num_of_action)
        {
        		return  num_of_agent/num_of_action;               	
        }
        
        public static bool isMDO(int[] actionHolder, int num_of_action, int num_of_agent)
        {
           for(int i = 1; i < actionHolder.Length; i++ )
           {
              if(actionHolder[i] > numOfPlayerceiling(num_of_agent, num_of_action))
              {
                 return false;
              }
           }           
           return true;
        }
        public static void Test(int[] array)
        {
          array[0] = -1;
          }
    }
}
