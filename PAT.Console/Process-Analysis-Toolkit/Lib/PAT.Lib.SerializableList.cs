using System;
using System.Collections.Generic;
using System.Text;
using PAT.Common.Classes.Expressions.ExpressionClass;

//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
   [Serializable]
   public class SerializableList: ExpressionValue
    {
        public System.Collections.Generic.List<int> list;

        public int Field = 0;

        public int Property
        {
            get { return Field; }
            set { Field = value; }
        }

        //default constructor
        public SerializableList()
        {
            list = new System.Collections.Generic.List<int>();
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

                returnString += ",Field=" + Field;

                return returnString;
            }
        }

        //override
        public override string ToString()
        {
            return "[" + ExpressionID + "]";

        }

        public int Count()
        {
            return list.Count;
        }

	    public void Add(int element)
        {
           this.list.Add(element);
  
        }

        public int Get(int index)
        {
            return this.list[index];
        }
        
        public bool Contains(int element)
        {
            return this.list.Contains(element);
        }

        public SerializableList Concat(SerializableList list1, SerializableList list2)
        {
            if (list1 == null && list2 == null)
            {
                return new SerializableList();
            }
            else if (list1 == null)
            {
                return (SerializableList)list2.GetClone();
            
            }
            else if (list2 == null)
            {
                return (SerializableList)list1.GetClone();
            }
            else
            {
                SerializableList newList = new SerializableList();
                newList.list.AddRange(new System.Collections.Generic.List<int>(list1.list));
                newList.list.AddRange(new System.Collections.Generic.List<int>(list2.list));
                return newList;
            
            }
          
        }

        public void Remove(int element)
        {
            this.list.Remove(element);
        }
        
        public void RemoveAt(int index)
        {
            if (index >= 0 && index <= list.Count)
            {
                this.list.RemoveAt(index);
            }
            else
            {
                //throw PAT Runtime exception
                throw new RuntimeException("index is less than 0.o -index is equal to or greater than length of the list.");
            }

          
        }

  
    }
}
