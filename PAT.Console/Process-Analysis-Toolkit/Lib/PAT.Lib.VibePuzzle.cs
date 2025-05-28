using System;
using System.Collections.Generic;
using System.Text;
//the namespace must be PAT.Lib, the class and method names can be arbitrary
namespace PAT.Lib
{
    /// <summary>
    /// The math library that can be used in your model.
    /// all methods should be declared as public static.
    /// 
    /// The parameters must be of type "int", or "int array"
    /// The number of parameters can be 0 or many
    /// 
    /// The return type can be bool, int or int[] only.
    /// 
    /// The method name will be used directly in your model.
    /// e.g. call(max, 10, 2), call(dominate, 3, 2), call(amax, [1,3,5]),
    /// 
    /// Note: method names are case sensetive
    /// </summary>
    public class VibePuzzle{
    	
    	//check last row, if there is a empty space in between of some figures, then it's immediate death
		public static bool isDead(int[] board, int rows, int cols){
			bool foundNonEmpty=false;
			bool foundEmpty=false;  //must not be leading empty
			for(int i=0; i<cols; i++){
				int v = board[(rows-1)*cols+i];
				if(v==0 && foundNonEmpty) foundEmpty = true; //
				if(v!=0){
					if(foundEmpty) return true; //immediate death
					else foundNonEmpty=true; 
				}
			}
			return false; //still alive
		}
		public static int[] eliminate(int[] board, int rows, int cols){
			
			int em = 0;
			int r, c, count;
			bool go=true;
			
			while(go){
				go=false;
				
				
				//same figures in a row
				r=0;
				while(r<rows){
					count=0;
					c=1;
					while(c<cols){
						if(board[r*cols+c]!=em && board[r*cols+c]==board[r*cols+c-1]){
							count++;
						}
						else{//not the same as previous item
							if(count>=2){ //two dupliates + itself will be 3 items 
								go=true;
								//set those positions to empty
								var t=count;
								while(t>=0){
									board[r*cols+c-1-t]=em;
									
									t--;
								}
							}
							
							count=0;
						}
						
						c++;
						
					}
					
					
					//boundary: still the same as previous item	
					if(count>=2){ //two dupliates + itself will be 3 items 
						go=true;
						//set those positions to empty
						var t=count;
						while(t>=0){
							board[r*cols+c-1-t]=em;
							
							t--;
						}
					}
					
					
					r++;
				}
				
				
				
				//same figures in a column
				c=0;
				while(c<cols){
					count=0;
					r=1;
					while(r<rows){
						if(board[r*cols+c]!=em && board[r*cols+c]==board[(r-1)*cols+c]){
							count++;
						}
						else{//not the same as previous item
							if(count>=2){ //two dupliates + itself will be 3 items 
								go=true;
								//set those positions to empty
								var t=count;
								while(t>=0){
									board[(r-1-t)*cols+c]=em;
									
									t--;
								}
							}
							
							count=0;
						}
						
						r++;
						
					}
					
					//boundary: still the same as previous item		
					if(count>=2){ //two dupliates + itself will be 3 items 
						go=true;
						//set those positions to empty
						var t=count;
						while(t>=0){
							board[(r-1-t)*cols+c]=em;
							
							t--;
						}
					}
					
					
					c++;
				}
				
				//move down
				if(go){ //some figures are eliminated
					r=rows-1;  //check from last row, then up to second-to-top row
					while(r>0){
						c=0;
						while(c<cols){
							if(board[r*cols+c]==em){
								for(int rr=r-1; rr>=0; rr--){
									if(board[rr*cols+c]!=em){
										board[r*cols+c] = board[rr*cols+c] ;
										board[rr*cols+c]  = em;
										break;
									}
								}
							}
							
							c++;
						}
						
						r--;
					}
				}
				
			}        		
        
			return board;
        }
    }
}
