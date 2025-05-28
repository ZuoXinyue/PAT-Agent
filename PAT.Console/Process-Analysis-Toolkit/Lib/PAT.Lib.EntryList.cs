using System;
using PAT.Common.Classes.Expressions.ExpressionClass;


//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    public class EntryList : ExpressionValue
    {

        public Entry[] array;


        //default constructor
        public EntryList()
        {
            array = null;
        }

        public EntryList(int n, int min, int max)
        {
            array = new Entry[n];
            for (int i = 0; i < n; i++)
            {
                array[i] = new Entry();
            }

            array[0].key = min;
            array[0].next = n - 1;
            array[n - 1].key = max;
        }



        public void Assign(int lhs, int rhs)
        {
            IncRC(rhs);
            DecRC(lhs);

        }

        private void IncRC(int reff)
        {
            if (reff != 0 && reff != array.Length - 1)
            {
                array[reff].reff++;
            }
        }

        public void DecRC(int reff)
        {
            if (reff != 0 && reff != array.Length - 1)
            {
                array[reff].reff--;
                if (array[reff].reff == 0)
                {
                    Gc(reff);
                }

            }
        }

        private void Gc(int i)
        {
            int curr = i;

            /*
            if (curr == 0)
            {
                curr = array[curr].next;
                array[curr].reff--;
            }
            */

            while (curr != 0 && curr < array.Length - 1 && array[curr].reff == 0)
            {
                int pred = curr;
                curr = array[pred].next;

                array[pred].key = 0;
                array[pred].marked = false;
                array[pred].next = 0;
                // array[pred].reff = 0;

                if (curr != 0 && curr != array.Length - 1 && array[curr].reff != 0)
                {
                    array[curr].reff--;
                }
            }


        }

        public void Reset(int i)
        {
            DecRC(i);

        }

        public void Reset3(int i, int j, int k)
        {
            DecRC(i);
            DecRC(j);
            DecRC(k);
        }

        public void Reset2(int i, int j)
        {
            DecRC(i);
            DecRC(j);
        }


        public int Next(int i)
        {

            return array[i].next;
        }

        public int GetNext(int lhs, int i)
        {
            int temp = lhs;
            int l = array[i].next;
            IncRC(l);
            DecRC(temp);
            return l;
        }


        public void SetNext(int i, int next)
        {
            int temp = array[i].next;
            array[i].next = next;
            IncRC(next);
            DecRC(temp);

        }


        public int Key(int i)
        {
            return array[i].key;
        }

        public void SetKey(int i, int key)
        {
            array[i].key = key;
        }

        public bool Marked(int i)
        {
            return array[i].marked;
        }

        public void SetMarked(int i, bool marked)
        {
            array[i].marked = marked;
        }

        public int Create(int target, int key, int next)
        {
            int returnValue = 0;
            for (int i = 1; i < array.Length - 1; i++)
            {
                if (array[i].reff == 0 && array[i].key == 0)
                {
                    array[i].key = key;
                    array[i].next = next;
                    array[i].reff = 1;
                    array[next].reff++;
                    returnValue = i;
                    break;
                }
            }

            if (returnValue == 0)
            {
                throw new PAT.Common.Classes.Expressions.ExpressionClass.RuntimeException("Out of memory. Need to prelocate more objects");
            }

            if (target != 0 && array[target].reff != 0)
            {
                DecRC(target);
            }


            return returnValue;
        }


        public int GetData()
        {
            if (array == null || array.Length < 2)
                return 0;

            int value = 0;
            int i = array[0].next;
            while (i != array.Length - 1 && array[i].key != 0)
            {
                value = value | (array[i].key);
                value = value << 2;
                i = array[i].next;
            }
            value = value >> 2;

            int returnValue = 0;
            for (int j = 0; j < 16; j++)
            {
                returnValue += ((int)Math.Pow(10, j)) * (3 & value);
                value = value >> 2;
                if (value == 0) break;
            }

            return returnValue;
        }


        public override string ExpressionID
        {
            get
            {
                if (array == null || array.Length < 2)
                { return ""; }


                //List<string> entries = new List<string>();
                //entries.Add(array[0].next.ToString());
                //for (int i = 1; i < array.Length-1; i++)
                //{
                //    if (array[i].reff <= 0) continue;

                //    entries.Add(array[i].ToString());
                //}


                //return String.Join(",", entries.ToArray());

                string returnString = array[0].next + ",";
                string copy = returnString;

                for (int i = 1; i < array.Length - 1; i++)
                {
                    if (array[i].reff <= 0) continue;
                    returnString += array[i].ExpressionID + ",";
                }

                if (returnString.Equals(copy))
                {
                    return "";
                }

                return returnString.Substring(0, returnString.Length - 1);
                //if (returnString.Length > 0)
                //{
                //    returnString = returnString.Substring(0, returnString.Length - 1);
                //}




                //return returnString;
            }
        }

        ////override
        //public override string GetID()
        //{


        //    if (array == null || array.Length < 2)
        //    { return ""; }


        //    //List<string> entries = new List<string>();
        //    //entries.Add(array[0].next.ToString());
        //    //for (int i = 1; i < array.Length-1; i++)
        //    //{
        //    //    if (array[i].reff <= 0) continue;

        //    //    entries.Add(array[i].ToString());
        //    //}

            
        //    //return String.Join(",", entries.ToArray());

        //    string returnString = array[0].next + ",";
        //    string copy = returnString;

        //    for (int i = 1; i < array.Length - 1; i++)
        //    {
        //        if (array[i].reff <= 0) continue;
        //        returnString += array[i].GetID() + ",";
        //    }

        //    if (returnString.Equals(copy))
        //    {
        //        return "";
        //    }

        //    return returnString.Substring(0, returnString.Length - 1);
        //    //if (returnString.Length > 0)
        //    //{
        //    //    returnString = returnString.Substring(0, returnString.Length - 1);
        //    //}

           


        //    //return returnString;
        //}


        //override
        public override string ToString()
        {
            return "[" + ExpressionID + "]";

        }

        //override
        public override ExpressionValue GetClone()
        {
            EntryList list = new EntryList();
            if (array == null)
            {
                return list;
            }
            list.array = new Entry[array.Length];
            for (int i = 0; i < array.Length; i++)
            {
                list.array[i] = (Entry)array[i].GetClone();
            }

            return list;
        }

    }


    public class Entry : ExpressionValue
    {
        public int key;

        public int next;

        public bool marked;

        public int reff = 0;

        //default constructor
        public Entry()
        {
            key = 0; marked = false; next = 0;
        }

        public Entry(int k)
        {
            key = k; marked = false; next = 0;
        }





        /// <summary>
        /// Please implement this method to provide the string representation of the datatype
        /// </summary>
        /// <returns></returns>
        public override string ToString()
        {
            return "(" + ExpressionID   + ")";
        }


        /// <summary>
        /// Please implement this method to return a deep clone of the current object
        /// </summary>
        /// <returns></returns>
        public override ExpressionValue GetClone()
        {
            Entry copy = new Entry();
            copy.key = this.key;
            copy.marked = this.marked;
            copy.next = this.next;
            copy.reff = this.reff;
            return copy;

        }

        public override string ExpressionID
        {
            get
            {
                int m = 0;

                if (marked)
                {
                    m = 1;
                }

                return key.ToString() + m.ToString() + next.ToString() + reff.ToString();
            }
        }


        ///// <summary>
        ///// Please implement this method to provide the compact string representation of the datatype
        ///// </summary>
        ///// <returns></returns>
        //public override string GetID()
        //{
        //    int m = 0;

        //    if (marked)
        //    {
        //        m = 1;
        //    }

        //    return key.ToString() + m.ToString() + next.ToString() + reff.ToString();

        //}

    }


}

