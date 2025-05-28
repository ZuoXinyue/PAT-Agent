#define CONTRACTS_FULL 
using System;
using System.Text;
using System.Collections.Generic;
using PAT.Common.Classes.Expressions.ExpressionClass;
using System.Diagnostics.Contracts; /* chengbin */
using System.Diagnostics;

//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
 public class Set : ExpressionValue
    {
        public System.Collections.Generic.List<int> list;

        //default constructor
        public Set()
        {
            this.list = new System.Collections.Generic.List<int>();
            Contract.Ensures(false,"this is contract false"); 
        }

        public Set(System.Collections.Generic.List<int> list)
        {
            this.list = list;
        }

        public override string ExpressionID
        {
            get
            {
                String returnString = "";
                foreach (int element in list)
                {
                    returnString += element.ToString() + ",";
                }

                if (returnString.Length > 0)
                {
                    returnString = returnString.Substring(0, returnString.Length - 1);
                }

                return returnString;
            }
        }

        ////overide
        //public override string GetID()
        //{
        //    String returnString = "";
        //    foreach (int element in list)
        //    {
        //        returnString += element.ToString() + ",";
        //    }

        //    if (returnString.Length > 0)
        //    {
        //        returnString = returnString.Substring(0, returnString.Length - 1);
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
            return new Set(new System.Collections.Generic.List<int>(list));
        }

        
        /// <summary>
        /// Add an element to a set
        /// </summary>
        /// <param name="element"></param>
        /// <returns></returns>
        public void Add(int element)
        {
            if (!this.list.Contains(element))
            {
                this.list.Add(element);
            }
            
        }

        /// <summary>
        /// Remove an element from a set
        /// </summary>
        /// <param name="element"></param>
        /// <returns></returns>
        public void Remove(int element)
        {
            if (this.list.Contains(element))
            {
                this.list.Remove(element);
            }
            
        }

        /// <summary>
        /// Union two sets
        /// </summary>
        /// <param name="set1"></param>
        /// <param name="set2"></param>
        /// <returns></returns>
        public  Set Union(Set set1, Set set2)
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
                foreach (int element in set1.list) 
                {
                    newSet.Add(element);    
                }

                foreach (int element in set2.list)
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
        public  Set Intersect(Set set1, Set set2)
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
                foreach(int element in set1.list)
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
        public  Set Substract(Set set1, Set set2)
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
            
            foreach (int element in set2.list)
            {
                if (newSet.list.Contains(element))
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
        public  bool Contains(int element)
        {
            return this.list.Contains(element);
        }


        /// <summary>
        /// Test whether set1 and set2 has common element or not
        /// </summary>
        /// <param name="set2"></param>
        /// <returns></returns>
        public bool IsOverlapping(Set set2)
        {
            foreach (int element in list)
            {
                foreach (int i in set2.list)
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
        public bool IsDisjoint( Set set2)
        {
            foreach (int element in list)
            {
                foreach (int i in set2.list)
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
