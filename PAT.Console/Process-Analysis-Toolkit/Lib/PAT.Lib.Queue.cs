using System;
using System.Collections.Generic;
using System.Text;
using PAT.Common.Classes.Expressions.ExpressionClass;

//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    public class Queue: ExpressionValue
    {
        public System.Collections.Generic.Queue<int> queue;
        
        //default constructor
        public Queue() 
        {
            this.queue = new System.Collections.Generic.Queue<int>();
        }
        
        public Queue(System.Collections.Generic.Queue<int> queue)
        {
            this.queue = queue;
        }

        //override

        public override ExpressionValue  GetClone()
        {
 	         return new Queue(new System.Collections.Generic.Queue<int>(this.queue) );
        }


        public override string  ToString()
        {
            return "[" + ExpressionID + "]";
        }


        public override string ExpressionID
        {
            get
            {
                string returnString = "";
                foreach (int element in this.queue)
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

        //public override string GetID()
        //{
        //    string returnString = "";
        //    foreach (int element in this.queue)
        //    {
        //        returnString += element.ToString() + ",";
        //    }
        //    if (returnString.Length > 0)
        //    {
        //        returnString = returnString.Substring(0, returnString.Length - 1);
        //    }

        //    return returnString;
        //}

         public void Enqueue(int element)
        {
            this.queue.Enqueue(element);
        }

        public void Dequeue()
        {
            if (this.queue.Count > 0)
            {
                queue.Dequeue();
            }
            else
            {
            
                //throw PAT Runtime exception
                throw new RuntimeException("Access an empty queue!");
            }

        }

        public bool Contains(int element)
        {
            return this.queue.Contains(element);
        }

        public Queue Concat(Queue q1, Queue q2)
        {
           if (q1 == null & q2 == null)
           {
                return new Queue();
           }
           else if (q1 == null)
           {
                return (Queue)q2.GetClone();
           }
           else if (q2 == null)
           {
                return (Queue)q1.GetClone();
           }
           else
           {
                Queue newQueue = (Queue) q1.GetClone();
                foreach(int element in q2.queue)
                {
                    newQueue.queue.Enqueue(element);
                }

               return newQueue;
           
           }
            
        }


        public int First()
        {
            if (this.queue.Count > 0)
            {
                return this.queue.ToArray()[0];
            }
            else
            {
            
                //throw PAT Runtime exception
                throw new RuntimeException("Access an empty queue!");
                
            }

        }

        public int Last()
        {
            if (queue.Count > 0)
            {
                return this.queue.ToArray()[queue.Count -1];
            }
            else 
            {
                //throw PAT Runtime exception
                throw new RuntimeException("Access an empty queue!");
              
            }
            
        }

        public void Clear()
        {
            this.queue.Clear();
        }

        public int Count()
        {
            return queue.Count;
        }
    
    }
}
