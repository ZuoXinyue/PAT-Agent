using System;
using System.Collections.Generic;
using PAT.Common.Classes.Expressions.ExpressionClass;

//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    /// <summary>
    /// A (sorted) Set, which gurranttees the GetID is same for sets with same elements
    /// </summary>
    public class Set : ExpressionValue
    {
        public SortedList<int, bool> list;
        
        //default constructor
        public Set()
        {
            this.list = new SortedList<int, bool>();
        }

        public Set(SortedList<int, bool> list)
        {
            this.list = list;
        }

        public int GetData()
        {

            int value = 0;
            foreach (int element in list.Keys)
            {
                value = value | element;
                value = value << 2;
            }

            value = value >> 2;

            int returnValue = 0;
            for (int i = 0; i < 16; i++)
            {
                returnValue += ((int)Math.Pow(10, i))  *( 3 & value);
                value = value >> 2;
                if (value == 0) break;
            }

            return returnValue;
        }

        public override string ExpressionID
        {
            get
            {
                String returnString = "";

                int size = list.Count - 1;
                for (int i = 0; i <= size; i++)
                {
                    int element = list.Keys[i];
                    if (i == size)
                    {
                        returnString += element;
                    }
                    else
                    {
                        returnString += element + ",";
                    }
                }

                return returnString;
            }
        }

        ////override
        //public override string GetID()
        //{
        //    String returnString = "";

        //    int size = list.Count - 1;
        //    for (int i = 0; i <= size; i++)
        //    {
        //        int element = list.Keys[i];
        //        if (i == size)
        //        {
        //            returnString += element;
        //        }
        //        else
        //        {
        //            returnString += element + ",";
        //        }
        //    }

        //    return returnString;
        //}

        //override
        public override string ToString()
        {
            return "[" + ExpressionID + "]";
        }


        //override
        public override ExpressionValue GetClone()
        {
            return new Set(new SortedList<int, bool>(list));
        }


        /// <summary>
        /// Add an element to a set
        /// </summary>
        /// <param name="element"></param>
        /// <returns></returns>
        public bool Add(int element)
        {
            if (!this.list.ContainsKey(element))
            {
                this.list.Add(element, false);
                return true;
            }
            return false;
        }

        public int Get(int index)
        {
            return this.list.Keys[index];
        }

        public int Count()
        {
            return list.Count;
        }

        public int[] GetSubsetByIndex(int index)
        {
            SortedList<int, bool> subset = new SortedList<int, bool>();

            int digitNumber = 0;
            while (index >= 1 && digitNumber < this.list.Count)
            {
                bool hasBit = index % 2 == 1;
                index = (int)(index / 2);
                if (hasBit)
                {
                    subset.Add(this.list.Keys[digitNumber], false);
                }
                digitNumber++;
            }

            this.list = subset;
            List<int> result = new List<int>(subset.Keys);
            return result.ToArray();
        }

        /// <summary>
        /// Remove an element from a set
        /// </summary>
        /// <param name="element"></param>
        /// <returns></returns>
        public bool Remove(int element)
        {
            if (this.list.ContainsKey(element))
            {
                this.list.Remove(element);
                return true;
            }

            return false;

        }

        /// <summary>
        /// Union two sets
        /// </summary>
        /// <param name="set1"></param>
        /// <param name="set2"></param>
        /// <returns></returns>
        public Set Union(Set set1, Set set2)
        {
            if (set1 == null && set2 == null)
            {
                return new Set();
            }
            else if (set1 == null)
            {
                return (Set)set2.GetClone();
            }
            else if (set2 == null)
            {
                return (Set)set1.GetClone();
            }
            else
            {
                Set newSet = new Set();
                foreach (int element in set1.list.Keys)
                {
                    newSet.Add(element);
                }

                foreach (int element in set2.list.Keys)
                {
                    newSet.Add(element);
                }

                return newSet;
            }
        }

        /// <summary>
        /// Do the intersection of two sets
        /// </summary>
        /// <param name="set1"></param>
        /// <param name="set2"></param>
        /// <returns></returns>
        public Set Intersect(Set set1, Set set2)
        {

            if (set1 == null && set2 == null)
            {
                return new Set();
            }
            else if (set1 == null)
            {
                return (Set)set2.GetClone();
            }
            else if (set2 == null)
            {
                return (Set)set1.GetClone();
            }
            else
            {
                Set newSet = new Set();
                foreach (int element in set1.list.Keys)
                {
                    if (set2.Contains(element))
                    {
                        newSet.Add(element);
                    }
                }

                return newSet;
            }

        }

        /// <summary>
        /// Substract set2 from set1
        /// </summary>
        /// <param name="set1"></param>
        /// <param name="set2"></param>
        /// <returns></returns>
        public Set Substract(Set set1, Set set2)
        {
            if (set1 == null)
            {
                return new Set();
            }

            if (set2 == null)
            {
                return (Set)set1.GetClone();
            }

            Set newSet = (Set)set1.GetClone();

            foreach (int element in set2.list.Keys)
            {
                if (newSet.list.ContainsKey(element))
                {
                    newSet.list.Remove(element);
                }

            }

            return newSet;


        }

        /// <summary>
        /// Test whether set contains the element
        /// </summary>
        /// <param name="element"></param>
        /// <returns></returns>
        public bool Contains(int element)
        {
            return this.list.ContainsKey(element);
        }


        /// <summary>
        /// Test whether set1 and set2 has common element or not
        /// </summary>
        /// <param name="set2"></param>
        /// <returns></returns>
        public bool IsOverlapping(Set set2)
        {
            foreach (int element in list.Keys)
            {
                foreach (int i in set2.list.Keys)
                {
                    if (i == element)
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        /// <summary>
        /// Test whether set1 and set2 has no common element or not
        /// </summary>
        /// <param name="set2"></param>
        /// <returns></returns>
        public bool IsDisjoint(Set set2)
        {
            foreach (int element in list.Keys)
            {
                foreach (int i in set2.list.Keys)
                {
                    if (i == element)
                    {
                        return false;
                    }
                }
            }

            return true;
        }
    }
}
