//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    /// <summary>
    /// You can use static library in PAT model.
    /// All methods should be declared as public static.
    /// 
    /// The parameters must be of type "int", "bool", "int[]" or user defined data type
    /// The number of parameters can be 0 or many
    /// 
    /// The return type can be void, bool, int, int[] or user defined data type
    /// 
    /// The method name will be used directly in your model.
    /// e.g. call(max, 10, 2), call(dominate, 3, 2), call(amax, [1,3,5]),
    /// 
    /// Note: method names are case sensetive
    /// </summary>
    public class Array
    {
        /// <summary>
        /// Return the length of the array
        /// </summary>
        /// <param name="array"></param>
        /// <returns></returns>
        public static int ArrayLength(int[] array)
        {
            return array.Length;
        }

        /// <summary>
        /// Test whether the array is of size 0 or not
        /// </summary>
        /// <param name="array"></param>
        /// <returns></returns>
        public static bool IsArrayEmpty(int[] array)
        {
            return array.Length == 0;
        }

        /// <summary>
        /// Return the max element in an array
        /// </summary>
        /// <param name="array"></param>
        /// <returns></returns>
        public static int ArrayMax(int[] array)
        {
            int max = array[0];
            foreach (int v in array)
            {
                if (max < v)
                {
                    max = v;
                }
            }
            return max;
        }

        /// <summary>
        /// Return the min element in an array
        /// </summary>
        /// <param name="array"></param>
        /// <returns></returns>
        public static int ArrayMin(int[] array)
        {
            int min = array[0];
            foreach (int v in array)
            {
                if (min > v)
                {
                    min = v;
                }
            }
            return min;
        }
    }
}
