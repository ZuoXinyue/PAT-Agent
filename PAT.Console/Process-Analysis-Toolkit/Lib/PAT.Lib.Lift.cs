using System;
using PAT.Common.Classes.Expressions.ExpressionClass;

//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    /// // <summary>
    /// User defined data type allows you to model any data structures in PAT.
    /// To create a user defined data type, you need to inherit ExpressionValue class and implement the necessary methods.
    ///
    /// After create a user defined data type, you can use it in PAT, e.g. "var<HashTable> table";
    /// To manipulate the variable, you can call its methods, e.g. "table.Add(3, 1)"
    ///
    /// Note: method names are case sensetive
    /// </summary>
    public class LiftControl : ExpressionValue
    {
        //-1; for not assigned; i for assigned to i-lift;
        int[] ExternalRequestsUp;
        int[] ExternalRequestsDown;
        //0; for not pressed, 1 for pressed
        int[][] InternalRequests;
        //0 for stopped at ground level; ready to go up.
        int[] LiftStatus;

        public LiftControl()
        {
            ExternalRequestsUp = new int[2];
            ExternalRequestsDown = new int[2];
            InternalRequests = new int[2][];
            InternalRequests[0] = new int[2];
            InternalRequests[1] = new int[2];
            LiftStatus = new int[2];
        }

        public LiftControl(int levels, int lifts)
        {
            ExternalRequestsUp = new int[levels];
            ExternalRequestsDown = new int[levels]; ;

            for (int i = 0; i < levels; i++)
            {
                ExternalRequestsUp[i] = -1;
                ExternalRequestsDown[i] = -1;
            }
            ;
            InternalRequests = new int[lifts][];
            LiftStatus = new int[lifts];

            for (int i = 0; i < lifts; i++)
            {
                InternalRequests[i] = new int[levels];
            }
        }

        public LiftControl(int[] externalRequestsUp, int[] externalRequestsDown, int[][] internalRequests, int[] liftStatus)
        {
            ExternalRequestsUp = new int[externalRequestsUp.Length]; ;

            for (int i = 0; i < ExternalRequestsUp.Length; i++)
            {
                ExternalRequestsUp[i] = externalRequestsUp[i];
            }

            ExternalRequestsDown = new int[externalRequestsDown.Length]; ;

            for (int i = 0; i < ExternalRequestsDown.Length; i++)
            {
                ExternalRequestsDown[i] = externalRequestsDown[i];
            }

            InternalRequests = new int[internalRequests.Length][];

            for (int i = 0; i < internalRequests.Length; i++)
            {
                InternalRequests[i] = new int[internalRequests[i].Length];

                for (int j = 0; j < internalRequests[i].Length; j++)
                {
                    InternalRequests[i][j] = internalRequests[i][j];
                }
            }

            LiftStatus = new int[liftStatus.Length];

            for (int i = 0; i < LiftStatus.Length; i++)
            {
                LiftStatus[i] = liftStatus[i];
            }
        }

        public override string ExpressionID
        {
            get
            {
                string toReturn = "";

                for (int i = 0; i < ExternalRequestsUp.Length; i++)
                {
                    toReturn += ExternalRequestsUp[i].ToString();
                }

                for (int i = 0; i < ExternalRequestsDown.Length; i++)
                {
                    toReturn += ExternalRequestsDown[i].ToString();
                }

                for (int i = 0; i < InternalRequests.Length; i++)
                {
                    for (int j = 0; j < InternalRequests[i].Length; j++)
                    {
                        toReturn += InternalRequests[i][j].ToString();
                    }
                }

                //foreach (int i in LiftStatus)
                //{
                //    toReturn += i;
                //}

                return toReturn;
            }
        }

        public override string ToString()
        {
            string toReturn = "";

            if (ExternalRequestsDown != null)
            {
                toReturn += "External Up Requests: ";
                for (int i = 0; i < ExternalRequestsUp.Length; i++)
                {
                    toReturn += ExternalRequestsUp[i] + " ";
                }

                toReturn += "\r\nExternal Down Requests: ";

                for (int i = 0; i < ExternalRequestsDown.Length; i++)
                {
                    toReturn += ExternalRequestsDown[i] + " ";
                }

                toReturn += "\r\n Internal Requests:";

                for (int i = 0; i < InternalRequests.Length; i++)
                {
                    toReturn += "\r\n Internal requests for " + i + " lift: ";
                    for (int j = 0; j < InternalRequests[i].Length; j++)
                    {
                        toReturn += InternalRequests[i][j] + " ";
                    }
                }

                toReturn += "\r\n Lift Status: ";

                for (int i = 0; i < LiftStatus.Length; i++)
                {
                    toReturn += LiftStatus[i] + " ";
                }
            }

            return toReturn;
        }

        public override ExpressionValue GetClone()
        {
            return new LiftControl(ExternalRequestsUp, ExternalRequestsDown, InternalRequests, LiftStatus);
        }

        public int HasAssignment(int lift)
        {
            for (int i = 0; i < ExternalRequestsUp.Length; i++)
            {
                if (ExternalRequestsUp[i] == lift || ExternalRequestsDown[i] == lift)
                {
                    return 1;
                }

                if (InternalRequests[lift][i] > 0)
                {
                    return 1;
                }
            }

            return 0;
        }

        public int KeepMoving(int lift, int level, int up)
        {
            if (level == ExternalRequestsUp.Length - 1 && up > 0)
            {
                return 0;
            }

            if (level == 0 && up < 1)
            {
                return 0;
            }

            if (up > 0)
            {
                for (int i = level + 1; i < ExternalRequestsUp.Length; i++)
                {
                    if (InternalRequests[lift][i] == 1)
                    {
                        return 1;
                    }

                    if (ExternalRequestsUp[i] == lift || ExternalRequestsDown[i] == lift)
                    {
                        return 1;
                    }
                }
            }
            else
            {
                for (int i = level - 1; i >= 0; i--)
                {
                    if (InternalRequests[lift][i] == 1)
                    {
                        return 1;
                    }

                    if (ExternalRequestsDown[i] == lift || ExternalRequestsUp[i] == lift)
                    {
                        return 1;
                    }
                }
            }

            return 0;
        }

        public void ClearRequests(int lift, int level, int up)
        {
            InternalRequests[lift][level] = 0;

            if (up > 0)
            {
                ExternalRequestsUp[level] = -1;
            }
            else
            {
                ExternalRequestsDown[level] = -1;
            }
        }

        public int isToOpenDoor(int lift, int level)
        {
            if (InternalRequests[lift][level] == 1)
            {
                return 0;
            }

            if (LiftStatus[lift] >= 0)
            {
                if (ExternalRequestsUp[level] == lift)
                {
                    return 1;
                }

                return 2;
            }

            if (ExternalRequestsDown[level] == lift)
            {
                return 3;
            }

            return 4;
        }

        public int PassBy (int lift, int level, int up)
        {
            //if (isToOpenDoor(lift, level) == 0)
            //{
                if (up > 0)
                {
                    if (ExternalRequestsUp[level] != lift && ExternalRequestsUp[level] >= 0)
                    {
                        return 1;
                    }
                }
                else
                {
                    if (ExternalRequestsDown[level] >= 0 && ExternalRequestsDown[level] == lift)
                    {
                        return 1;
                    }
                }                
            //}

            return 0;
        }

        public void AddInternalRequest(int lift, int level)
        {
            InternalRequests[lift][level] = 1;
        }

        public int UpdateLiftStatus(int lift, int level, int direction)
        {
            LiftStatus[lift] = LiftStatus[lift] + 1;

            return PassBy(lift, level, direction);
        }

        public void ChangeDirection(int lift)
        {
            LiftStatus[lift] = LiftStatus[lift] * -1;
        }

        public void AddExternalRequest(int level, int lift, int up)
        {
            if (up > 0)
            {
                ExternalRequestsUp[level] = lift;
            }
            else
            {
                ExternalRequestsDown[level] = lift;
            }
        }

        public void AssignExternalRequest(int level, int up) // 1 for going up
        {
            if (up > 0)
            {
                if (ExternalRequestsUp[level] >= 0)
                {
                    return;
                } 
            }

            if (up < 1)
            {
                if (ExternalRequestsDown[level] >= 0)
                {
                    return;
                }
            }

            //at ground floor, pusing down is not possible
            if (level == 0 && up < 1)
            {
                return;
            }

            //at top floor, pusing up is not possible
            if (level == ExternalRequestsUp.Length - 1 && up > 0)
            {
                return;
            }

            int minimumDistance = int.MaxValue;
            int chosenLift = -1;

            for (int i = 0; i < LiftStatus.Length; i++)
            {
                int distance;

                if (up > 0)
                {
                    if (LiftStatus[i] >= 0)
                    {
                        if (LiftStatus[i] <= level)
                        {
                            distance = level - LiftStatus[i];
                        }
                        else
                        {
                            distance = LiftStatus.Length - LiftStatus[i] + LiftStatus.Length - level;
                        }
                    }
                    else
                    {
                        distance = LiftStatus[i] * -1 + level;
                    }
                }
                else
                {
                    if (LiftStatus[i] >= 0)
                    {
                        distance = LiftStatus.Length - LiftStatus[i] + LiftStatus.Length - level;
                    }
                    else
                    {
                        if (LiftStatus[i] <= level)
                        {
                            distance = -1 * level - LiftStatus[i];
                        }
                        else
                        {
                            distance = LiftStatus[i] * -1 + level;
                        }
                    }
                }

                if (distance < minimumDistance)
                {
                    chosenLift = i;
                    minimumDistance = distance;
                }
            }

            if (up > 0)
            {
                ExternalRequestsUp[level] = chosenLift;
            }
            else
            {
                ExternalRequestsDown[level] = chosenLift;
            }
        }
    }
}