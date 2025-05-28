using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using PAT.Common.Classes.Expressions.ExpressionClass;
using PAT.Common.Classes.DataStructure;
using PAT.Common.Classes.Ultility;
using System.Diagnostics.Contracts; 

//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    public class DBM : ExpressionValue
    {
        public List<int> TimerArray;
        public static bool TimedRefinementAssertion;

        public bool IsEmpty
        {
            get
            {
                return TimerArray == null;
            }
        }

        //matrix to store the 
        public List<List<int>> Matrix;

        //if DBM is empty, it is in connoicalform
        public bool IsCanonicalForm = true;

        //the ceiling of the values in the DBM
        public int Ceiling;

        public DBM(int ceiling)
        {
            Ceiling = ceiling;
        }


        public DBM(List<int> idArray, List<List<int>> matrix, bool isCanonical)
        {
            TimerArray = idArray;
            Matrix = matrix;
            IsCanonicalForm = isCanonical;
        }

        /// <summary>
        /// Get the number of Timers in the DBM
        /// </summary>
        /// <returns></returns>
        public int GetTimerCount()
        {
            if (TimerArray == null)
            {
                return 0;
            }
            return TimerArray.Count;
        }


        /// <summary>
        /// Return the next avaiable TimerID
        /// Old timer ID can be reused if possible
        /// </summary>
        /// <returns></returns>
        public int GetNewTimerID()
        {
            if (TimerArray == null)
            {
                return 1;
            }

            int dimention = TimerArray.Count;
						
            if (TimedRefinementAssertion)
            {
                for (int k = 1; k <= dimention; k++)
                {
                    if (Matrix[k][0] == 0 && Matrix[0][k] == 0 && TimerArray[k - 1] != 1)
                    {
                        return TimerArray[k - 1];
                    }
                }
            }
            else
            {
                for (int k = 1; k <= dimention; k++)
                {
                    if (Matrix[k][0] == 0 && Matrix[0][k] == 0)
                    {
                        return TimerArray[k - 1];
                    }
                }
            }

            List<int> temp = new List<int>(TimerArray);
            temp.Sort();

            int timerCounter = 1;
            foreach (int i in temp)
            {
                if (i > timerCounter)
                {
                    break;
                }
                timerCounter++;
            }

            Contract.Assert(timerCounter > 0, "Get New Timer ID Failure");
			
            return timerCounter;
        }

        /// <summary>
        /// Add a new timer id 
        /// </summary>
        /// <param name="timerID"></param>
        public void AddTimer(int timerID)
        {
            Contract.Ensures(IsCanonicalForm, "Add Timer Failure: DBM is not in Canonical Form!");

            if (TimerArray == null)
            {
                //initialize the system
                TimerArray = new List<int>(4);
                Matrix = new List<List<int>>(4);
                List<int> constantRow = new List<int>(4);
                constantRow.Add(0);
                Matrix.Add(constantRow);
            }
            else
            {
                if (TimerArray.Contains(timerID))
                {
                    if (!this.IsCanonicalForm)
                    {
                        this.GetCanonicalForm();
                    }
                    return;
                }

                /**************************************
                //add the last column to be maxvalue
                Matrix[0].Add(0);
                for (int i = 1; i < Matrix.Count; i++)
                {
                    //Matrix[i].Add(int.MaxValue);
                    Matrix[i].Add(Matrix[i][0]);
                }
                ***************************************/
            }

            if (!this.IsCanonicalForm)
            {
                this.GetCanonicalForm();
            }

            Matrix[0].Add(0);
            for (int i = 1; i < Matrix.Count; i++)
            {
                Matrix[i].Add(Matrix[i][0]);
            }

            TimerArray.Add(timerID);


            List<int> newTimerRow = new List<int>(Matrix[0].Count);
            //the last row are all 0
            //newTimerRow.AddRange(new int[TimerArray.Count + 1]);
            for (int i = 0; i < Matrix[0].Count; i++)
            {
                newTimerRow.Add(Matrix[0][i]);
            }

            //add the last row
            Matrix.Add(newTimerRow);
        }

        /// <summary>
        /// Reset the Timer to 0
        /// </summary>
        /// <param name="timerid"></param>
        public void ResetTimer(int timerid)
        {
            Contract.Requires(this.IsCanonicalForm, "Reset Timer Pre-Condition Failure: DBM is not in Canonical Form!");

            int dimention = TimerArray.Count;
            int timerID = TimerArray.IndexOf(timerid) + 1;

            Matrix[timerID][0] = 0;
            Matrix[0][timerID] = 0;

		
            for (int i = 1; i <= dimention; i++)
            {
                Matrix[i][timerID] = Matrix[i][0];
                Matrix[timerID][i] = Matrix[0][i];
            }
        }

        public void GetClockInterval(int timerid, Intervals intervals)
        {
            int timerID = TimerArray.IndexOf(timerid) + 1;
            intervals.AddInterval(Matrix[0][timerID] * -1, Matrix[timerID][0]);
        }

        /// <summary>
        /// Get the canonical form of the DBM
        /// </summary>
        private void GetCanonicalForm()
        {
            int dimention = TimerArray.Count;
            for (int k = 0; k <= dimention; k++)
            {
                for (int i = 0; i <= dimention; i++)
                {
                    for (int j = 0; j <= dimention; j++)
                    {
                        //check for the overflow problem
                        if (Matrix[i][k] != int.MaxValue && Matrix[k][j] != int.MaxValue)
                        {
                            //Attension, Matrix[i][k] + Matrix[k][j] is bigger than int.MaxValue, there is a possbility of overflow.
                            int oldValue = Matrix[i][j];
                            Matrix[i][j] = Math.Min(Matrix[i][j], Matrix[i][k] + Matrix[k][j]);
                            
                            if(Matrix[i][j] > Ceiling)
                            {
                                Matrix[i][j] = int.MaxValue;
                            }
                            if(Matrix[i][j] < -1* Ceiling)
                            {
                                Matrix[i][j] = 0;
                            }

                            if(i == 0)
                            {
                                Debug.Assert(Matrix[i][j] != int.MaxValue, i + ":" + j + ":" + k + "==" + oldValue +":"+ Matrix[i][j] + ":" + Matrix[i][k] + ":" + Matrix[k][j] + "Checking failed!!!" + ToString());
                            }
                        }
                    }
                }
            }


            IsCanonicalForm = true;
        }



        /// <summary>
        /// Update the DBM with a new constraint
        /// </summary>
        /// <param name="timerID">which timer the constraint is on</param>
        /// <param name="op">0 for equal; 1 for >=; 2 for <=</param>
        /// <param name="constant"></param>
        public void AddConstraint(int timerID, int op, int constant)
        {
			
            Contract.Assert(timerID != 0, "Add Constraint Failure: Timer ID is 0");

            int timer = TimerArray.IndexOf(timerID) + 1;
            Contract.Assert(timer > 0, "Add Constraint Failure: Timer Index (" + timer + ") is out of range!");
			

            switch (op)
            {
                case 0:
                    if (Matrix[timer][0] > constant)
                    {
                        Matrix[timer][0] = constant;
                    }

                    if (Matrix[0][timer] > -1 * constant)
                    {
                        Matrix[0][timer] = -1 * constant;
                    }

                    break;
                case 1:
                    if (Matrix[0][timer] > -1 * constant)
                    {
                        Matrix[0][timer] = -1 * constant;
                    }

                    break;
                case 2:
                    if (Matrix[timer][0] > constant)
                    {
                        Matrix[timer][0] = constant;
                    }
                    break;
            }

            IsCanonicalForm = false;
        }
        /// <summary>
        /// Check whether the DBM satisfies a given primitive constraint 
        /// </summary>
        /// <param name="timerID"></param>
        /// <param name="op"></param>
        /// <param name="constant"></param>
        public bool Implies(int timerID, int op, int constant)
        {
            if (!IsCanonicalForm)
            {
                GetCanonicalForm();
            }

            int timer = TimerArray.IndexOf(timerID) + 1;

            switch (op)
            {
                case 0:
                    return Matrix[timer][0] == constant && Matrix[0][timer] == -1 * constant;
                case -1:
                    return Matrix[0][timer] <= -1 * constant;
                default: //1:
                    return Matrix[timer][0] <= constant;
            }
        }

        public void Delay()
        {
            Contract.Requires(this.IsCanonicalForm, "Delay Failure"); 
			if (TimerArray != null)
            {
                for (int i = 1; i <= TimerArray.Count; i++)
                {
                    Matrix[i][0] = int.MaxValue;
                }
            }
        }

       
        public DBM KeepTimers(int[] activeTimer)
        {
            Contract.Requires(this.IsCanonicalForm, "Keep Timers Failure");

            List<int> idArray = new List<int>();
            List<List<int>> newMatrix = new List<List<int>>(4);


            List<int> temp = new List<int>();
            temp.Add(0);

            foreach (int timerID in activeTimer)
            {
                int timerIndex = this.TimerArray.IndexOf(timerID) + 1;
                idArray.Add(timerID);
                temp.Add(timerIndex);
            }

            foreach (int i in temp)
            {
                List<int> constantRow = new List<int>(4);
                foreach (int j in temp)
                {
                    constantRow.Add(Matrix[i][j]);
                }
                newMatrix.Add(constantRow);
            }

            return new DBM(idArray, newMatrix, true);
        }
		
		
        public bool IsConstraintNotSatisfied()
        {
            if (TimerArray == null)
            {
                return false;
            }

            if (!IsCanonicalForm)
            {
                GetCanonicalForm();
            }

            return Matrix[0][0] < 0;

        }

        public bool IsTimersBounded(int bound)
        {
            for (int i = 1; i <= TimerArray.Count; i++)
            {
                if ((Matrix[0][i] != int.MinValue && Math.Abs(Matrix[0][i]) > bound) || (Matrix[i][0] != int.MaxValue && Math.Abs(Matrix[i][0]) > bound))
                {
                    return false;
                }
            }
            return true;
        }

        public bool IsSubSetOf(DBM myDBM)
        {
            Contract.Requires(this.IsCanonicalForm, "IsSubSetOf Failure");
            Contract.Requires(myDBM.IsCanonicalForm, "IsSubSetOf Failure");
			

            if (myDBM.TimerArray == null)
            {
                return true;
            }

            if (this.TimerArray == null)
            {
                return false;
            }

            for (int i = 0; i < myDBM.TimerArray.Count; i++)
            {
                int index = TimerArray.IndexOf(myDBM.TimerArray[i]) + 1;
                if (index != 0)
                {
                    if (Matrix[index][0] > myDBM.Matrix[i + 1][0] || Matrix[0][index] > myDBM.Matrix[0][i + 1])
                    {
                        return false;
                    }
                }
                else
                {
                    return false;
                }
            }

            return true;
        }
        
        public void Conjunction(DBM myDBM)
        {
            if (myDBM.TimerArray == null)
            {
                return;
            }

            if (TimerArray == null)
            {
                Matrix = myDBM.Matrix;
                TimerArray = myDBM.TimerArray;
                IsCanonicalForm = myDBM.IsCanonicalForm;
            }
            else if (myDBM.TimerArray != null)
            {
                Contract.Assert(TimerArray.Count == myDBM.TimerArray.Count, "//Contract-12");    /* chengbin3 */
                int dimention = TimerArray.Count;
                for (int i = 0; i < dimention; i++)
                {
                    int myith = i + 1;
                    int ith = TimerArray.IndexOf(myDBM.TimerArray[i]) + 1;

                    for (int j = 0; j < dimention; j++)
                    {
                        int myjth = j + 1;
                        int jth = TimerArray.IndexOf(myDBM.TimerArray[j]) + 1;

                        if (Matrix[ith][jth] > myDBM.Matrix[myith][myjth])
                        {
                            Matrix[ith][jth] = myDBM.Matrix[myith][myjth];
                        }
                    }
                }

                for (int i = 0; i < dimention; i++)
                {
                    int myith = i + 1;
                    int ith = TimerArray.IndexOf(myDBM.TimerArray[i]) + 1;

                    if (Matrix[0][ith] > myDBM.Matrix[0][myith])
                    {
                        Matrix[0][ith] = myDBM.Matrix[0][myith];
                    }

                    if (Matrix[ith][0] > myDBM.Matrix[myith][0])
                    {
                        Matrix[ith][0] = myDBM.Matrix[myith][0];
                    }
                }

                IsCanonicalForm = false;
            }			
        }

        public override String ToString()
        {
            if (TimerArray == null)
            {
                return "";
            }

            StringBuilder sb = new StringBuilder();
            List<int> temp = new List<int>(TimerArray);
            temp.Sort();

            for (int i = 1; i <= temp.Count; i++)
            {
                int timerId = temp[i - 1];
                int j = TimerArray.IndexOf(timerId) + 1;
                sb.AppendLine("clock" + timerId + ":[" + Matrix[0][j]*-1 + "," + (Matrix[j][0] == int.MaxValue ? Constants.INFINITE : Matrix[j][0].ToString()) + "];");
            }

            return sb.ToString();
        }

        /// <summary>
        /// Please implement this method to return a deep clone of the current object
        /// </summary>
        /// <returns></returns>
        public override ExpressionValue GetClone()
        {
            return Clone();
        }

        public DBM Clone()
        {
            if (TimerArray == null)
            {
                return new DBM(Ceiling);
            }

            List<List<int>> newMatrix = new List<List<int>>();
            for (int i = 0; i < Matrix.Count; i++)
            {
                List<int> newRow = new List<int>();
                for (int j = 0; j < Matrix.Count; j++)
                {
                    newRow.Add(Matrix[i][j]);
                }
                newMatrix.Add(newRow);
            }

            return new DBM(new List<int>(this.TimerArray), newMatrix, IsCanonicalForm);
        }

        public override string ExpressionID
        {
            get
            {
                if (TimerArray == null)
                {
                    return "";
                }

                string toReturn = "";
                List<int> temp = new List<int>(TimerArray);
                temp.Sort();

                for (int i = 1; i <= temp.Count; i++)
                {
                    int timerId = temp[i - 1];
                    int j = TimerArray.IndexOf(timerId) + 1;
                    toReturn += timerId + "[" + Matrix[0][j] * -1 + "," + Matrix[j][0] + "]";
                }

                return toReturn;
            }
        }

        ///// <summary>
        ///// Please implement this method to provide the compact string representation of the datatype
        ///// </summary>
        ///// <returns></returns>
        //public override string GetID()
        //{
        //    if (TimerArray == null)
        //    {
        //        return "";
        //    }

        //    string toReturn = "";
        //    List<int> temp = new List<int>(TimerArray);
        //    temp.Sort();

        //    for (int i = 1; i <= temp.Count; i++)
        //    {
        //        int timerId = temp[i - 1];
        //        int j = TimerArray.IndexOf(timerId) + 1;
        //        toReturn += timerId + "[" + Matrix[0][j] * -1 + "," + Matrix[j][0] + "]";
        //    }

        //    return toReturn;
        //}

       

        public bool GetIsCanonicalForm()
        {
            return IsCanonicalForm;
        }

        public int FalseCanonicalForm()
        {
            IsCanonicalForm = false;			
			return 0;
        }

        //[//ContractInvariantMethod]
        //protected void ObjectInvariant()
        //{
        //    //Contract.Invariant(!IsCanonicalForm || (IsCanonicalForm && isCF()));
        //}

        //private bool isCF()
        //{
        //    bool temp = true;
        //    int dimention = 0;
        //    if (TimerArray != null)
        //    {
        //        dimention = TimerArray.Count;
        //    }
        //    else
        //    {
        //        return true;
        //    }

        //    for (int k = 0; k <= dimention & temp; k++)
        //    {
        //        for (int i = 0; i <= dimention & temp; i++)
        //        {
        //            for (int j = 0; j <= dimention & temp; j++)
        //            {
        //                try
        //                {
        //                    if (Matrix[i][k] != int.MaxValue && Matrix[k][j] != int.MaxValue)
        //                    {
        //                        if (Matrix[i][j] != Math.Min(Matrix[i][j], Matrix[i][k] + Matrix[k][j]))
        //                        {
        //                            temp = false;
        //                        }
        //                    }
        //                }
        //                catch (Exception e)
        //                { 
        //                    //chengbin3 - just make it compile
        //                    throw new PAT.Common.Classes.Expressions.ExpressionClass.OutOfMemoryException(e.Message);
        //                }
        //            }
        //        }
        //    }

        //    return temp;
        //}

    }
}