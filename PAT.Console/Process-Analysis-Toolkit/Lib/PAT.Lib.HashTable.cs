using System;
using System.Collections;
using PAT.Common.Classes.Expressions.ExpressionClass;

//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    public class HashTable : ExpressionValue
    {
        public Hashtable table;

        public HashTable()
        {
            table = new Hashtable();
        }

        public HashTable(Hashtable newTable)
        {
            table = newTable;
        }

        public void Add(int key, int value)
        {
            if (!table.ContainsKey(key))
            {
                table.Add(key, value);
            }
        }

        public bool ContainsKey(int key)
        {
            return table.ContainsKey(key);
        }

        public int GetValue(int key)
        {
            return (int)table[key];
        }

        /// <summary>
        /// Return the string representation of the hash table.
        /// This method must be overriden
        /// </summary>
        /// <returns></returns>
        public override string ToString()
        {
            return "[" + ExpressionID + "]";

        }

        /// <summary>
        /// Return a deep clone of the hash table
        /// This method must be overriden
        /// </summary>
        /// <returns></returns>
        public override ExpressionValue GetClone()
        {
            return new HashTable(new Hashtable(table));
        }

        public override string ExpressionID
        {
            get
            {
                string returnString = "";
                foreach (DictionaryEntry entry in table)
                {
                    returnString += entry.Key + "=" + entry.Value + ",";
                }
                if (returnString.Length > 0)
                {
                    returnString = returnString.Substring(0, returnString.Length - 1);
                }
                return returnString;
            }
        }

        ///// <summary>
        ///// Return the compact string representation of the hash table.
        ///// This method must be overriden
        ///// Smart implementation of this method can reduce the state space and speedup verification 
        ///// </summary>
        ///// <returns></returns>
        //public override string GetID()
        //{
        //    string returnString = "";
        //    foreach (DictionaryEntry entry in table)
        //    {
        //        returnString += entry.Key + "=" + entry.Value + ",";
        //    }
        //    if (returnString.Length > 0)
        //    {
        //        returnString = returnString.Substring(0, returnString.Length - 1);
        //    }
        //    return returnString;
        //}

        
    }
}
