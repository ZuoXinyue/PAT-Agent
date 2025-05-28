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
    public class Board : ExpressionValue
    {
        int[] board = new int[] {-1,-1,1,1,-1,-1,-1,
                                 -1,-1,1,1,-1,-1,-1,
                                  1,1,1,0,1,1,1,
                                  1,0,1,1,1,0,1,
                                 -1,-1,1,0,-1,-1,-1,
                                 -1,-1,1,1,-1,-1,-1};

        int bposnX = 3;
        int bposnY;

        public Board()
        {

        }

        public Board(int[] newboard, int x, int y)
        {
            board = newboard;
            this.bposnX = x;
            this.bposnY = y;
        }

        public override string ExpressionID
        {
            get
            {
                string toReturn = bposnX + ";" + bposnY;
                for (int i = 0; i < 42; i++)
                {
                    if (board[i] == 0)
                    {
                        toReturn += "," + i;
                    }
                }

                return toReturn;
            }
        }

        //public override string GetID()
        //{
        //    string toReturn = bposnX + ";" + bposnY;
        //    for (int i = 0; i < 42; i++)
        //    {
        //        if (board[i] == 0)
        //        {
        //            toReturn += "," + i;
        //        }
        //    }

        //    return toReturn;
        //}

        public override string ToString()
        {
            string toReturn = "bposnX: " + bposnX + "\r\n";
            toReturn += "bposnY: " + bposnY + "\r\nboard:\r\n" ;

            toReturn += Common.Classes.Ultility.Ultility.PPStringList(board);
            return toReturn;
        }

        public override ExpressionValue GetClone()
        {
            return new Board(board.Clone() as int[], bposnX, bposnY);
        }

        public bool GameOver()
        {
            return board[16] == 0 && board[17] == 0 && board[23] == 0 && board[24] == 0;
        }

        public void MoveUp()
        {
            if (bposnX - 1 >= 0)
            {
                if (board[bposnY + (bposnX - 1) * 7] == 1)
                {
                    bposnX = (bposnX - 1);
                }
            }
        }

        public void PushUp()
        {
            if (bposnX - 2 >= 0)
            {
                if ((board[(bposnY + (7 * (bposnX - 2)))] == 1) && (board[(bposnY + (7 * (bposnX - 1)))] == 0))
                {
                    board[(bposnY + (7 * (bposnX - 2)))] = 0; board[(bposnY + (7 * (bposnX - 1)))] = 1; bposnX = (bposnX - 1);
                }
            }
        }

        public void MoveDown()
        {
            if (bposnX + 1 < 6)
            {
                if (board[(bposnY + (7 * (bposnX + 1)))] == 1)
                {
                    bposnX = (bposnX + 1);
                }
            }
        }

        public void PushDown()
        {
            if (bposnX + 2 < 6)
            {
                if ((board[(bposnY + (7 * (bposnX + 2)))] == 1) && (board[(bposnY + (7 * (bposnX + 1)))] == 0))
                {
                    board[(bposnY + (7 * (bposnX + 2)))] = 0; board[(bposnY + (7 * (bposnX + 1)))] = 1; bposnX = (bposnX + 1);
                }
            }
        }

        public void MoveLeft()
        {
            if (bposnY - 1 >= 0)
            {
                if (board[((bposnY - 1) + (7 * bposnX))] == 1)
                {
                    bposnY = (bposnY - 1);
                }
            }
        }

        public void PushLeft()
        {
            if (bposnY - 2 >= 0)
            {
                if ((board[((bposnY - 2) + (7 * bposnX))] == 1) && (board[((bposnY - 1) + (7 * bposnX))] == 0))
                {
                    board[((bposnY - 2) + (7 * bposnX))] = 0; board[((bposnY - 1) + (7 * bposnX))] = 1; bposnY = (bposnY - 1);
                }
            }
        }

        public void MoveRight()
        {
            if (bposnY + 1 < 7)
            {
                if (board[((bposnY + 1) + (7 * bposnX))] == 1)
                {
                    bposnY = (bposnY + 1);
                }
            }
        }

        public void PushRight()
        {
            if (bposnY + 2 < 7)
            {
                if ((board[((bposnY + 2) + (7 * bposnX))] == 1) && (board[((bposnY + 1) + (7 * bposnX))] == 0))
                {
                    board[bposnY + 2 + 7 * bposnX] = 0; board[((bposnY + 1) + (7 * bposnX))] = 1; bposnY = (bposnY + 1);
                }
            }
        }
    }
}