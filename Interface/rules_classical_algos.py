import re
def process_classical_algos(algo_id, var_value):
    if isinstance(var_value, str):
        try:
            var_value = int(var_value)
        except ValueError:
            pass
    if algo_id == "peterson":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        lines = []
        lines.append(f"#define N {var_value};")
        lines.append("")
        lines.append("var step[N];")
        lines.append("var pos[N];")
        lines.append("var counter = 0; //which counts how many processes are in the critical session.")
        
        # For each process from 0 to var_value-1
        for i in range(var_value):
            # Process definition line
            lines.append(f"Process{i}() = Repeat{i}(1); cs.{i}{{counter = counter+1;}} -> reset{{pos[{i}] = 0; counter = counter-1;}} -> Process{i}();")
            # First line of the Repeat procedure
            lines.append(f"Repeat{i}(j) = [j < N] update.{i}.1{{pos[{i}] = j;}} -> update.{i}.2{{step[j] = {i};}} -> ")
            # Construct the waiting branch condition:
            # It should check that for every other process k, pos[k] < j.
            cond_list = []
            for k in range(var_value):
                if k != i:
                    cond_list.append(f"pos[{k}] < j")
            condition = " && ".join(cond_list)
            # The waiting branch (indented by 16 spaces)
            lines.append(f"{' ' * 16}([step[j] != {i} || ({condition})]idle.j -> Repeat{i}(j+1))")
            # The alternative branch (indented by 8 spaces)
            lines.append(f"{' ' * 8}[] [j == N] Skip;")
            # Add a blank line between process blocks
            lines.append("")
        
        # Combine the processes in parallel
        process_names = " ||| ".join([f"Process{i}()" for i in range(var_value)])
        lines.append(f"Peterson() = {process_names};")
        lines.append("")
        lines.append("#define goal counter > 1;")
        lines.append("#assert Peterson() reaches goal;")
        lines.append("#assert Peterson() |= []<> cs.0;")
        
        processed_code = "\n".join(lines)

    elif algo_id == "dining_philosophers":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        lines = []
        # Header
        lines.append(f"#define N {var_value};")
        lines.append("")
        
        # Process definitions (Phil and Fork)
        lines.append("Phil(i) = get.i.(i+1)%N -> get.i.i -> eat.i -> put.i.(i+1)%N -> put.i.i -> Phil(i);")
        lines.append("Fork(x) = get.x.x -> put.x.x -> Fork(x) [] get.(x-1)%N.x -> put.(x-1)%N.x -> Fork(x);")
        lines.append("College() = ||x:{0..N-1}@(Phil(x)||Fork(x));")
        
        # Build the resource set for Implementation()
        tokens = []
        # For process 0: fixed tokens
        tokens.append("get.0.0")
        tokens.append("get.0.1")
        tokens.append("put.0.0")
        tokens.append("put.0.1")
        # For each process i from 1 to var_value-1:
        for i in range(1, var_value):
            tokens.append(f"eat.{i}")
            tokens.append(f"get.{i}.{i}")
            tokens.append(f"get.{i}.{(i+1) % var_value}")
            tokens.append(f"put.{i}.{i}")
            tokens.append(f"put.{i}.{(i+1) % var_value}")
        
        tokens_str = ",".join(tokens)
        lines.append(f"Implementation() = College() \\ {{{tokens_str}}};")
        
        # Specification and Properties (static text)
        lines.append("Specification() = eat.0 -> Specification();")
        lines.append("////////////////The Properties//////////////////")
        lines.append("#assert College() deadlockfree;")
        lines.append("#assert College() |= []<> eat.0;")
        lines.append("#assert Implementation() refines Specification();")
        lines.append("#assert Specification() refines Implementation();")
        lines.append("#assert Implementation() refines <F> Specification();")
        lines.append("#assert Specification() refines <F> Implementation();")
        lines.append("#assert Implementation() refines <FD> Specification();")
        lines.append("#assert Specification() refines <FD> Implementation();")

        processed_code = "\n".join(lines)

    elif algo_id == "milner_scheduler":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        lines = []
        # Header and alphabet declaration
        lines.append(f"#define N {var_value};")
        lines.append("#alphabet Cycle {ini.i,ini.(i+1)%N};")
        lines.append("")
        
        # Cycle0 and Cycle(i) definitions
        lines.append("Cycle0         = a.0 -> ini.1 -> work.0 -> ini.0 -> Cycle0;")
        lines.append("Cycle(i)         = ini.i -> a.i -> (work.i -> atomic{ini.(i+1)%N -> Skip}; Cycle(i) [] ini.(i+1)%N -> atomic{work.i -> Skip}; Cycle(i));")
        lines.append("MilnerAcyclic() = Cycle0 || (|| x:{1..N-1} @ Cycle(x)); ")
        
        # Build the token set for the Implementation() process.
        # It always starts with tokens for process 0 and then for each process from 1 to var_value-1
        tokens = []
        tokens.append("ini.0")
        tokens.append("a.0")
        for i in range(1, var_value):
            tokens.append(f"work.{i}")
            tokens.append(f"ini.{i}")
            tokens.append(f"a.{i}")
        tokens_str = ",".join(tokens)
        lines.append(f"Implementation()=(MilnerAcyclic() \\ {{{tokens_str}}});")
        
        # Specification definition
        lines.append("Specification()=(work.0->Specification());")
        lines.append("")
        
        # The Properties block (remains static)
        lines.append("////////////////The Properties//////////////////")
        lines.append("#assert MilnerAcyclic() deadlockfree;")
        lines.append("#assert MilnerAcyclic() |= []<>work.0;")
        lines.append("#assert Implementation() refines Specification();")
        lines.append("#assert Specification() refines Implementation();")
        lines.append("#assert Implementation() refines <F> Specification();")
        lines.append("#assert Specification() refines <F> Implementation();")
        lines.append("#assert Implementation() refines <FD> Specification();")
        lines.append("#assert Specification() refines <FD> Implementation();")

        processed_code = "\n".join(lines)

    elif algo_id == "readers_writers":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        lines = []
        lines.append(f"#define M {var_value};")
        lines.append("")
        lines.append("Writer() \t= startwrite -> stopwrite -> Writer();")
        lines.append("Reader() \t= startread -> stopread -> Reader();")
        lines.append("Reading(i) \t= [i == 0]Controller() []")
        lines.append("\t\t\t [i == M] stopread -> Reading(i-1) []")
        lines.append("\t\t\t [i > 0 && i < M] (startread -> Reading(i+1) [] stopread -> Reading(i-1));")
        lines.append("")
        lines.append("Controller() \t= startread -> Reading(1)")
        lines.append("\t\t\t [] stopread -> error -> Controller()")
        lines.append("\t\t\t [] startwrite -> (stopwrite -> Controller() [] stopread -> error -> Controller());")
        lines.append("")
        lines.append("ReadersWriters() = Controller() || (|||x:{0..M-1} @ (Reader() ||| Writer()));")
        lines.append("")
        lines.append("Implementation() \t= ReadersWriters() \\ {startread, stopread, startwrite, stopwrite};")
        lines.append("Specification() \t= error -> Specification();")
        lines.append("")
        lines.append("#alphabet Reading {startread,stopread};")
        lines.append("")
        lines.append("////////////////The Properties//////////////////")
        lines.append("#assert ReadersWriters() deadlockfree;")
        lines.append("#assert ReadersWriters() |= []<>error;")
        lines.append("#assert ReadersWriters() |= ![]<>error;")
        lines.append("#assert Implementation() refines Specification();")
        lines.append("#assert Specification() refines Implementation();")
        lines.append("#assert Implementation() refines <F> Specification();")
        lines.append("#assert Specification() refines <F> Implementation();")
        lines.append("#assert Implementation() refines <FD> Specification();")
        lines.append("#assert Specification() refines <FD> Implementation();")

        processed_code = "\n".join(lines)

    elif algo_id == "dijkstra":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        # Build the sum for the mutual exclusion property: "enter_cs[0] + enter_cs[1] + ... + enter_cs[var_value-1]"
        token_list = " + ".join([f"enter_cs[{i}]" for i in range(var_value)])
        
        # Template for Dijkstra's algorithm.
        # Note: Double curly braces {{ and }} produce literal { and } in the output.
        template = """#define N {N};

var flag[N];
var enter_cs[N];
var turn;

Process(i) = set_flag.i {{flag[i] = 1;}} -> (Check1(i) ; (set_flag.i {{flag[i] = 2;}} -> Check2(i, 0)));

Check1(i) = if(turn != i)				
            {{
                if(flag[turn] == 0)
                {{
                    get_turn{{turn = i;}} -> Skip
                }}
                else
                {{
                    Check1(i)
                }}
            }};

Check2(i, j) = 
    if(j==N)
    {{
        CS(i)
    }}
    else if(j == i)
    {{
        Check2(i, j+1)
    }}
    else if(flag[j] == 2)
    {{
        Process(i)
    }}
    else 
    {{
        Check2(i, j + 1)
    }};
    
CS(i) = cs.i{{enter_cs[i] = 1;}} -> exit.i {{flag[i] = 0; enter_cs[i]= 0;}} -> Process(i);


Dijkstra() = [] x:{{0..N-1}} @ (tau{{turn = x}} -> (|||y :{{0..N-1}}@Process(y))); 

//mutual exclution
#define p (({p_sum}) >= 2); 

#assert Dijkstra() deadlockfree;
#assert Dijkstra() reaches p;"""
        
        processed_code = template.format(N=var_value, p_sum=token_list)

    elif algo_id == "needham":
        if var_value.lower() == "original":
            processed_code = "enum {A, B, I, Na, Nb, gD};\n\n//ca: type 1 messages {x1,x2}PK{x3}\n//cb: type 2 messages {x1}PK{x2}\nchannel ca 0;\nchannel cb 0;\n\n//IniRunningAB is true iff initiator A takes part in a session of the protocol with B.\nvar IniRunningAB = false;\n//IniCommitAB is true iff initiator A commits to a session with B.\nvar IniCommitAB = false;\n//ResRunningAB is true iff responder B takes part in a session of the protocol with A.\nvar ResRunningAB = false;\n//ResCommitAB is true iff responder B commits to a session with A.\nvar ResCommitAB = false;\n\n//Initiator\nPIni(sender, receiver, nonce) =\n\tIniRunning_AB { if (sender == A && receiver == B) { IniRunningAB = true; } } ->\n\t//sending {nonce, sender}Pk{receiver}\n\tca!sender.nonce.sender.receiver ->\n\t\n\t//receiving {nonce, g1}Pk{sender}\n\tca?sender.nonce.g1.sender -> IniCommit_AB { if (sender == A && receiver == B) { IniCommitAB = true; } } ->\n\t\n\t//sending {g1}Pk{receiver}\n\tcb!sender.g1.receiver -> Skip;\n\n//Responder\nPRes(receiver, nonce) =\t\n\t//receiving {g2, g3}Pk{receiver}\n\tca?receiver.g2.g3.receiver ->\n\tResRunning_AB { if (g3 == A && receiver == B) { ResRunningAB = true; } } ->\n\t\n\t//sending {g2, nonce}Pk{g3}\n\tca!receiver.g2.nonce.g3 ->\n\t\n\t//receiving {nonce}Pk{receiver}\n\tcb?receiver.nonce.receiver ->\n\tResCommit_AB { if (g3 == A && receiver == B) { ResCommitAB = true; } } -> Skip;\n\n//Intruder knows Na\nvar kNa = false; \n//Intruder knows Nb\nvar kNb = false;\n//Intruder knows {Na, Nb}PK{A}\nvar k_Na_Nb__A = false;\n//Intruder knows {Na, A}PK{B}\nvar k_Na_A__B = false;\n//Intruder knows {Nb}PK{B}\nvar k_Nb__B = false;\n\n//Intruder Process, which always knows A, B, I, PK(A), PK(B), PK(I), SK(I) and Ng\nPI() =\n\tca!B.gD.A.B -> PI() []\n\tca!B.gD.B.B -> PI() []\n\tca!B.gD.I.B -> PI() []\n\t\n\tca!B.A.A.B -> PI []\n\tca!B.A.B.B -> PI []\n\tca!B.A.I.B -> PI []\n\t\n\tca!B.B.A.B -> PI() []\n\tca!B.B.B.B -> PI() []\n\tca!B.B.I.B -> PI() []\n\t\n\tca!B.I.A.B -> PI() []\n\tca!B.I.B.B -> PI() []\n\tca!B.I.I.B -> PI() []\n\t\n\t[kNa]                        ca!A.Na.Na.A -> PI() []\n\t[(kNa && kNb) || k_Na_Nb__A] ca!A.Na.Nb.A -> PI() []\n\t[kNa]                        ca!A.Na.gD.A -> PI() []\n\t\n\t[kNa] ca!A.Na.A.A -> PI() []\n\t[kNa] ca!A.Na.B.A -> PI() []\n\t[kNa] ca!A.Na.I.A -> PI() []\n\t\n\t[kNa || k_Na_A__B] ca!B.Na.A.B -> PI() []\n\t[kNa]              ca!B.Na.B.B -> PI() []\n\t[kNa]              ca!B.Na.I.B -> PI() []\n\t\n\t[kNb] ca!B.Nb.A.B -> PI() []\n\t[kNb] ca!B.Nb.B.B -> PI() []\n\t[kNb] ca!B.Nb.I.B -> PI() []\n\t\n\t[k_Nb__B || kNb] cb!B.Nb.B -> PI() []\n\t\n\tca?tmp1.x1.x2.x3\n\t-> InterceptChanA {\n\t\tif (x3 == I) {\n\t\t\tif (x1 == Na) { kNa = true; }\n\t\t\telse if (x1 == Nb) { kNb = true; }\n\t\t\tif (x2 == Na) { kNa = true; }\n\t\t\telse if (x2 == Nb) { kNb = true; }\n\t\t}\n\t\telse if (x1 == Na && x2 == A && x3 == B) { k_Na_A__B = true; }\n\t\telse if (x1 == Na && x2 == Nb && x3 == A) { k_Na_Nb__A = true; }\n\t}\n\t-> PI() []\n\t\n\tcb?tmp2.y1.y2\n\t-> InterceptChanB {\n\t\tif (y2 == I) {\n\t\t\tif (y1 == Na) { kNa = true; }\n\t\t\telse if (y1 == Nb) { kNb = true; }\n\t\t}\n\t\telse if (y1 == Nb && y2 == B) { k_Nb__B = true; }\n\t}\n\t-> PI();\n\nProtocol = ( PIni(A, I, Na) [] PIni(A, B, Na) ) ||| PRes(B, Nb) ||| PI;\n\n#define iniRunningAB (IniRunningAB == true);\n#define iniCommitAB (IniCommitAB == true);\n#define resRunningAB (ResRunningAB == true);\n#define resCommitAB (ResCommitAB == true);\n\n//Authentication of B to A can thus be expressed saying that ResRunningAB must become true before IniCommitAB.\n//i.e., the initiator A commits to a session with B only if B has indeed taken part in a run of the protocol with A.\n#assert Protocol |= [] ( ([] !iniCommitAB) || (!iniCommitAB U resRunningAB) );\n\n//The converse authentication property corresponds to saying that IniRunningAB becomes true before ResCommitAB.\n//The flaw of the protocol is shown by this model\n#assert Protocol |= [] ( ([] !resCommitAB) || (!resCommitAB U iniRunningAB) );\n\n#assert Protocol deadlockfree;"
        elif var_value.lower() == "fixed":
            processed_code =  "enum {A, B, I, Na, Nb, gD};\n\n//ca: type 1 messages {x1,x2}PK{x3}\n//cb: type 2 messages {x1}PK{x2}\n//cc: type 3 messages {x1,x2,x3}PK{x4}\nchannel ca 0;\nchannel cb 0;\nchannel cc 0;\n\n//IniRunningAB is true iff initiator A takes part in a session of the protocol with B.\nvar IniRunningAB = false;\n//IniCommitAB is true iff initiator A commits to a session with B.\nvar IniCommitAB = false;\n//ResRunningAB is true iff responder B takes part in a session of the protocol with A.\nvar ResRunningAB = false;\n//ResCommitAB is true iff responder B commits to a session with A.\nvar ResCommitAB = false;\n\n//Initiator\nPIni(sender, receiver, nonce) =\n\tIniRunning_AB { if (sender == A && receiver == B) { IniRunningAB = true; } } ->\n\t\n\t//sending {nonce, sender}Pk{receiver}\n\tca!sender.nonce.sender.receiver ->\n\t\n\t//receiving {nonce, g1}Pk{sender}\n\tcc?sender.nonce.g1.receiver.sender -> IniCommit_AB { if (sender == A && receiver == B) { IniCommitAB = true; } } ->\n\t\n\t//sending {g1}Pk{receiver}\n\tcb!sender.g1.receiver -> Skip;\n\n//Responder\nPRes(receiver, nonce) =\t\n\t//receiving {g2, g3}Pk{receiver}\n\tca?receiver.g2.g3.receiver -> ResRunning_AB { if (g3 == A && receiver == B) { ResRunningAB = true; } } ->\n\t\n\t//sending {g2, nonce, receiver}Pk{g3}\n\tcc!receiver.g2.nonce.receiver.g3 ->\n\t\t\n\t//receiving {nonce}Pk{receiver}\n\tcb?receiver.nonce.receiver -> ResCommit_AB { if (g3 == A && receiver == B) { ResCommitAB = true; } } -> Skip;\n\n//Intruder knows Na\nvar kNa = false; \n//Intruder knows Nb\nvar kNb = false;\n//Intruder knows {Na, Nb, B}PK{A}\nvar k_Na_Nb_B__A = false;\n//Intruder knows {Na, A}PK{B}\nvar k_Na_A__B = false;\n//Intruder knows {Nb}PK{B}\nvar k_Nb__B = false;\n\n//Intruder Process, which always knows A, B, I, PK(A), PK(B), PK(I), SK(I) and Ng\nPI() =\n\tca!B.gD.A.B -> PI() []\n\tca!B.gD.B.B -> PI() []\n\tca!B.gD.I.B -> PI() []\n\t\n\tca!B.A.A.B -> PI() []\n\tca!B.A.B.B -> PI() []\n\tca!B.A.I.B -> PI() []\n\t\n\tca!B.B.A.B -> PI() []\n\tca!B.B.B.B -> PI() []\n\tca!B.B.I.B -> PI() []\n\t\n\tca!B.I.A.B -> PI() []\n\tca!B.I.B.B -> PI() []\n\tca!B.I.I.B -> PI() []\n\t\n\t[kNa]                        cc!A.Na.Na.B.A -> PI() []\n\t[(kNa && kNb) || k_Na_Nb_B__A] cc!A.Na.Nb.B.A -> PI() []\n\t[kNa]                        cc!A.Na.gD.B.A -> PI() []\n\t\n\t[kNa] cc!A.Na.A.B.A -> PI() []\n\t[kNa] cc!A.Na.B.B.A -> PI() []\n\t[kNa] cc!A.Na.I.B.A -> PI() []\n\t\n\t[kNa]        cc!A.Na.Na.I.A -> PI() []\n\t[kNa && kNb] cc!A.Na.Nb.I.A -> PI() []\n\t[kNa]        cc!A.Na.gD.I.A -> PI() []\n\t\n\t[kNa] cc!A.Na.A.I.A -> PI() []\n\t[kNa] cc!A.Na.B.I.A -> PI() []\n\t[kNa] cc!A.Na.I.I.A -> PI() []\n\t\n\t[kNa || k_Na_A__B] ca!B.Na.A.B -> PI() []\n\t[kNa]              ca!B.Na.B.B -> PI() []\n\t[kNa]              ca!B.Na.I.B -> PI() []\n\t\n\t[kNb] ca!B.Nb.A.B -> PI() []\n\t[kNb] ca!B.Nb.B.B -> PI() []\n\t[kNb] ca!B.Nb.I.B -> PI() []\n\t\n\t[k_Nb__B || kNb] cb!B.Nb.B -> PI() []\n\t\n\tca?tmp1.x1.x2.x3\n\t-> InterceptChanA {\n\t\tif (x3 == I) {\n\t\t\tif (x1 == Na) { kNa = true; }\n\t\t\telse if (x1 == Nb) { kNb = true; }\n\t\t\tif (x2 == Na) { kNa = true; }\n\t\t\telse if (x2 == Nb) { kNb = true; }\n\t\t}\n\t\telse if (x1 == Na && x2 == A && x3 == B) { k_Na_A__B = true; }\n\t} -> PI() []\n\t\n\tcb?tmp2.y1.y2\n\t-> InterceptChanB {\n\t\tif (y2 == I) {\n\t\t\tif (y1 == Na) { kNa = true; }\n\t\t\telse if (y1 == Nb) { kNb = true; }\n\t\t}\n\t\telse if (y1 == Nb && y2 == B) { k_Nb__B = true; }\n\t} ->  PI() []\n\t\n\tcc?tmp3.z1.z2.z3.z4 \n\t-> InterceptChanC {\n\t\tif (z4 == I) {\n\t\t\tif (z1 == Na) { kNa = true; }\n\t\t\telse if (z1 == Nb) { kNb = true; }\n\t\t\tif (z2 == Na) { kNa = true; }\n\t\t\telse if (z2 == Nb) { kNb = true; }\n\t\t\tif (z3 == Na) { kNa = true; }\n\t\t\telse if (z3 == Nb) { kNb = true; }\n\t\t}\n\t\telse if (z1 == Na && z2 == Nb && z3 == B && z4 == A) { k_Na_Nb_B__A = true; }\n\t} -> PI;\n\nProtocol = ( PIni(A, I, Na) [] PIni(A, B, Na) ) ||| PRes(B, Nb) ||| PI;\n\n#define iniRunningAB (IniRunningAB == true);\n#define iniCommitAB (IniCommitAB == true);\n#define resRunningAB (ResRunningAB == true);\n#define resCommitAB (ResCommitAB == true);\n\n//Authentication of B to A can thus be expressed saying that ResRunningAB must become true before IniCommitAB.\n//i.e., the initiator A commits to a session with B only if B has indeed taken part in a run of the protocol with A.\n#assert Protocol |= [] ( ([] !iniCommitAB) || (!iniCommitAB U resRunningAB) );\n\n//The converse authentication property corresponds to saying that IniRunningAB becomes true before ResCommitAB.\n//The flaw of the protocol is shown by this model\n#assert Protocol |= [] ( ([] !resCommitAB) || (!resCommitAB U iniRunningAB) );\n\n#assert Protocol deadlockfree;"
        else:
            raise ValueError("Please enter a valid option!")
        
    elif algo_id == "interrupt_controller":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        
        processed_code = f"""#define MODULO {var_value};

// Input to the counter
channel up 0;
channel down 0;

// Shut down request
channel shutdown 0;

// Internal communication
channel i 0;

var noOfError = 0;

var count;

Int = shutdown?0 -> i!0 -> Stop;

C = up?0 {{count = (count + 1) % MODULO;}} -> C [] down?0 {{if(count > 0) {{count = count - 1;}}}} -> C [] i?0 -> Stop;

Evn = up!0 -> Evn [] down!0 -> Evn []  shutdown!0 -> ( up!0 -> Error() [] down!0 -> Error());

Error = error{{noOfError++}} -> Stop;

aSys = Int ||| C ||| Evn;

#define goal noOfError > 0;
#assert aSys reaches goal;"""

    elif algo_id == "abp":
        if var_value < 1:
            raise ValueError("Please enter a valid number which is at least 2!")
        
        processed_code = f"""#define CHANNELSIZE {var_value};

channel c CHANNELSIZE; //unreliable channel.
channel d CHANNELSIZE; //perfect channel.
channel tmr 0; //a synchronous channel between sender and timer, which is used to implement premature timeout.

Sender(alterbit) = (c!alterbit -> Skip [] lost -> Skip);
                                  tmr!1 -> Wait4Response(alterbit);

Wait4Response(alterbit) = (d?x -> ifa (x==alterbit) {{
                                      tmr!0 -> Sender(1-alterbit)
                                  }} else {{
                                      Wait4Response(alterbit)
                                  }})
                          [] tmr?2 -> Sender(alterbit);

Receiver(alterbit) = c?x -> ifa (x==alterbit) {{
                                 d!alterbit -> Receiver(1-alterbit)
                            }} else {{
                                 Receiver(alterbit)
                            }};

Timer = tmr?1 -> (tmr?0 -> Timer [] tmr!2 -> Timer);

ABP = Sender(0) ||| Receiver(0) ||| Timer;

#assert ABP deadlockfree;
#assert ABP |= []<> lost;"""

    elif algo_id == "tpcp":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        
        processed_code = f"""#define N {var_value}; //number of pages
enum {{Yes, No, Commit, Abort}}; //constants
//channel result 0;
//channel inform 0;
channel vote 0;
var hasNo = false;
 
//The following models the coordinator 
Coord(decC) = (|||{{N}}@ request -> Skip); 
              (|||{{N}}@ vote?vo -> atomic{{tau{{if (vo == No) {{hasNo = true;}}}} -> Skip}}); 
              decide -> 
              (([hasNo == false] (|||{{N}}@inform.Commit -> Skip); CoordPhaseTwo(Commit)) [] ([hasNo == true] (|||{{N}}@inform.Abort -> Skip); CoordPhaseTwo(Abort)));
CoordPhaseTwo(decC) = |||{{N}}@acknowledge -> Skip;
 
//The following models a page
Page(decP, stable) = request -> execute -> (vote!Yes -> PhaseTwo(decP) [] vote!No -> PhaseTwo(decP));
PhaseTwo(decP) = inform.Commit -> complete -> result.decP -> acknowledge -> Skip
                         [] inform.Abort -> undo -> result.decP -> acknowledge -> Skip;
 
#alphabet Coord {{request, inform.Commit, inform.Abort, acknowledge}};
#alphabet Page {{request, inform.Commit, inform.Abort, acknowledge}};
                        
System = Coord(Abort) || (|||{{N}}@Page(Abort, true));
Implementation = System \\{{request, execute, acknowledge, inform.Abort, inform.Commit, decide, result.Abort, result.Commit}};
 
#assert System deadlockfree;
#define has hasNo == 1;
#assert System |= [](has -> <> undo);
#assert System |= [](request -> <> undo);
 
Specification = PC(N);
PC(i) = [i == 0](|||{{N}}@complete -> Skip)
        []
        [i > 0]  (vote.Yes -> PC(i-1) [] vote.No -> PU(i-1));
PU(i) = [i == 0](|||{{N}}@undo -> Skip)
        []
        [i > 0](vote.Yes -> PU(i-1) [] vote.No -> PU(i-1));
#assert Specification deadlockfree;
 
#assert Implementation refines Specification;"""

    elif algo_id == "multi_register_1r_1w":
        try:
            var_value, implementation_type, event_type = re.split(r'[,\s]+', var_value.strip())
            var_value = int(var_value)
            implementation_type = implementation_type.lower()
            event_type = event_type.lower()
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (var_value < 3) or (implementation_type not in ['faulty', 'correct']) or (event_type not in ['tau', 'explicit']):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        if implementation_type == 'correct' and event_type == 'tau':
            lines = []
            # Define the shared binary array of size N.
            # Create an array with all 0's except the last entry is 1.
            b_elements = [ "0" for _ in range(var_value - 1) ] + ["1"]
            b_array = "[" + ",".join(b_elements) + "]"
            lines.append("//shared binary array of size N")
            lines.append(f"var B = {b_array};")
            lines.append("")
            lines.append("//register value used by the abstract model")
            lines.append(f"var R = {var_value - 1};")
            lines.append("//temporary value for abstract reader to stored the value read from register")
            lines.append("var M = 0;")
            lines.append("")
            
            # Concrete Implementation Model
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            lines.append("Readers() = read_inv -> UpScan(0);")
            lines.append("UpScan(i) = if(B[i] == 1) { DownScan(i - 1, i) } else { UpScan(i + 1) };")
            lines.append("DownScan(i, v) =")
            lines.append("\tif(i >= 0) {")
            lines.append("\t\tif(B[i] == 1) { DownScan(i - 1, i) } else { DownScan(i - 1, v) }")
            lines.append("\t} else {")
            lines.append("\t\tread_res.v -> Readers()")
            lines.append("\t};")
            lines.append("")
            lines.append("Writer(i) = write_inv.i -> tau{B[i] = 1;} -> WriterDownScan(i-1);")
            lines.append("WriterDownScan(i) = if(i >= 0) { tau{B[i] = 0;} -> WriterDownScan(i-1) } else { write_res -> Skip };")
            lines.append("")
            # Generate the list of Writers depending on var_value.
            writer_list = "[]".join([f"Writer({i})" for i in range(var_value)])
            lines.append(f"Writers() = ({writer_list}); Writers();")
            lines.append("Register() = Readers() ||| Writers();")
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("ReadersAbs() = read_inv -> tau{M=R;} -> read_res.M -> ReadersAbs();")
            lines.append("")
            lines.append("WriterAbs(i) = write_inv.i -> tau{R=i;} -> write_res -> Skip;")
            lines.append("")
            # Generate the list of WriterAbs processes.
            writer_abs_list = "[]".join([f"WriterAbs({i})" for i in range(var_value)])
            lines.append(f"WritersAbs() = ({writer_abs_list}); WritersAbs();")
            lines.append("RegisterAbs() = ReadersAbs() ||| WritersAbs();")
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Register() refines RegisterAbs();")
            lines.append("#assert RegisterAbs() refines Register();")

            processed_code = "\n".join(lines)

        elif implementation_type == 'correct' and event_type == 'explicit':
            lines = []
            # Shared array and register values
            lines.append("//shared binary array of size N")
            # Create an array with var_value-1 zeros and a final 1.
            b_array = "[" + ",".join(["0"] * (var_value - 1) + ["1"]) + "]"
            lines.append(f"var B = {b_array};")
            lines.append("//register value used by the abstract model")
            lines.append(f"var R = {var_value - 1};")
            lines.append("//temporary value for abstract reader to stored the value read from register")
            lines.append("var M = 0;")
            lines.append("")
            
            # Concrete Implementation Model
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            lines.append("Readers() = read_inv -> UpScan(0);")
            lines.append("UpScan(i) = if(B[i] == 1) { DownScan(i - 1, i) } else { UpScan(i + 1) };")
            lines.append("DownScan(i, v) =")
            lines.append("\tif(i >= 0) {")
            lines.append("\t\tif(B[i] == 1) { DownScan(i - 1, i) } else { DownScan(i - 1, v) }")
            lines.append("\t} else {")
            lines.append("\t\tread_res.v -> Readers()")
            lines.append("\t};")
            lines.append("")
            lines.append("Writer(i) = write_inv.i -> write.i.1{B[i] = 1;} -> WriterDownScan(i-1);")
            lines.append("WriterDownScan(i) = if(i >= 0) { write.i.0{B[i] = 0;} -> WriterDownScan(i-1) } else { write_res -> Skip };")
            lines.append("")
            
            # Writers process: list of Writer(i) separated by "[]"
            writer_list = "[]".join([f"Writer({i})" for i in range(var_value)])
            lines.append(f"Writers() = ({writer_list}); Writers();")
            
            # Register: concrete implementation hiding a set of write actions.
            # For each i in 0..var_value-1, include tokens: write.i.0 and write.i.1.
            concrete_tokens = []
            for i in range(var_value):
                concrete_tokens.append(f"write.{i}.0")
                concrete_tokens.append(f"write.{i}.1")
            tokens_concrete = ", ".join(concrete_tokens)
            lines.append(f"Register() = (Readers() ||| Writers()) \\{{{tokens_concrete}}};")
            lines.append("")
            
            # Abstract Specification Model
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("ReadersAbs() = read_inv -> read{M=R;} -> read_res.M -> ReadersAbs();")
            lines.append("")
            lines.append("WriterAbs(i) = write_inv.i -> write.i{R=i;} -> write_res -> Skip;")
            # List WriterAbs(i) for all pages.
            writer_abs_list = "[]".join([f"WriterAbs({i})" for i in range(var_value)])
            lines.append(f"WritersAbs() = ({writer_abs_list}); WritersAbs();")
            lines.append("")
            
            # RegisterAbs: abstract register hiding a different set.
            # Tokens: for each i in 0..var_value-1, include "write.i" and then add "read".
            abstract_tokens = [f"write.{i}" for i in range(var_value)]
            abstract_tokens.append("read")
            tokens_abstract = ", ".join(abstract_tokens)
            lines.append(f"RegisterAbs() = (ReadersAbs() ||| WritersAbs()) \\{{{tokens_abstract}}};")
            lines.append("")
            
            # Properties
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Register() refines RegisterAbs();")
            lines.append("#assert RegisterAbs() refines Register();")

            processed_code = "\n".join(lines)

        elif implementation_type == 'faulty' and event_type == 'tau':
            lines = []
            # Shared binary array and register parameters
            lines.append("//shared binary array of size N")
            # B array: (var_value-1) zeros and a final 1
            b_array = "[" + ",".join(["0"] * (var_value - 1) + ["1"]) + "]"
            lines.append(f"var B = {b_array};")
            lines.append("//register value used by the abstract model")
            lines.append(f"var R = {var_value - 1};")
            lines.append("//temporary value for abstract reader to stored the value read from register")
            lines.append("var M = 0;")
            lines.append("")
            
            # Concrete Implementation Model
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            lines.append("Readers() = read_inv -> UpScan(0);")
            lines.append("UpScan(i) = if(B[i] == 1) { read_res.i -> Readers() } else { UpScan(i + 1) };")
            lines.append("")
            lines.append("Writer(i) = write_inv.i -> tau{B[i] = 1;} -> WriterDownScan(i-1);")
            lines.append("WriterDownScan(i) = if(i >= 0) { tau{B[i] = 0;} -> WriterDownScan(i-1) } else { write_res -> Skip };")
            lines.append("")
            
            # Generate the Writers process list: Writer(0)[]Writer(1)...[]Writer(var_value-1)
            writers = "[]".join([f"Writer({i})" for i in range(var_value)])
            lines.append(f"Writers() = ({writers}); Writers();")
            lines.append("Register() = Readers() ||| Writers();")
            
            # Abstract Specification Model
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("ReadersAbs() = read_inv -> tau{M=R;} -> read_res.M -> ReadersAbs();")
            lines.append("")
            lines.append("WriterAbs(i) = write_inv.i -> tau{R=i;} -> write_res -> Skip;")
            # Generate the WritersAbs process list similarly: WriterAbs(0)[]WriterAbs(1)...[]WriterAbs(var_value-1)
            writers_abs = "[]".join([f"WriterAbs({i})" for i in range(var_value)])
            lines.append(f"WritersAbs() = ({writers_abs}); WritersAbs();")
            lines.append("RegisterAbs() = ReadersAbs() ||| WritersAbs();")
            
            # Properties
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Register() refines RegisterAbs();")
            lines.append("#assert RegisterAbs() refines Register();")

            processed_code = "\n".join(lines)

        else: # faulty & explicit
            lines = []
            # Shared binary array and register parameters
            lines.append("//shared binary array of size N")
            # Create an array with (var_value-1) zeros followed by a single 1
            b_array = "[" + ",".join(["0"] * (var_value - 1) + ["1"]) + "]"
            lines.append(f"var B = {b_array};")
            lines.append("//register value used by the abstract model")
            lines.append(f"var R = {var_value - 1};")
            lines.append("//temporary value for abstract reader to stored the value read from register")
            lines.append("var M = 0;")
            lines.append("")
            
            # Concrete Implementation Model
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            lines.append("Readers() = read_inv -> UpScan(0);")
            lines.append("UpScan(i) = if(B[i] == 1) { read_res.i -> Readers() } else { UpScan(i + 1) };")
            lines.append("")
            lines.append("Writer(i) = write_inv.i -> write.i.1{B[i] = 1;} -> WriterDownScan(i-1);")
            lines.append("WriterDownScan(i) = if(i >= 0) { write.i.0{B[i] = 0;} -> WriterDownScan(i-1) } else { write_res -> Skip };")
            lines.append("")
            
            # Writers process: list Writer(0)[]Writer(1)[]...[]Writer(var_value-1)
            writer_list = "[]".join(f"Writer({i})" for i in range(var_value))
            lines.append(f"Writers() = ({writer_list}); Writers();")
            
            # Register (concrete) with hiding of write tokens for each Writer
            # For each page i, we hide actions write.i.0 and write.i.1.
            concrete_tokens = []
            for i in range(var_value):
                concrete_tokens.append(f"write.{i}.0")
                concrete_tokens.append(f"write.{i}.1")
            hiding_concrete = ", ".join(concrete_tokens)
            lines.append(f"Register() = (Readers() ||| Writers()) \\{{{hiding_concrete}}};")
            lines.append("")
            
            # Abstract Specification Model
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("ReadersAbs() = read_inv -> read{M=R;} -> read_res.M -> ReadersAbs();")
            lines.append("")
            lines.append("WriterAbs(i) = write_inv.i -> write.i{R=i;} -> write_res -> Skip;")
            # WritersAbs: list WriterAbs(0)[]WriterAbs(1)[]...[]WriterAbs(var_value-1)
            writer_abs_list = "[]".join(f"WriterAbs({i})" for i in range(var_value))
            lines.append(f"WritersAbs() = ({writer_abs_list}); WritersAbs();")
            lines.append("")
            
            # RegisterAbs with hiding of abstract write tokens and the read action.
            # For each page i, hide action write.i; then also hide "read"
            abstract_tokens = [f"write.{i}" for i in range(var_value)]
            abstract_tokens.append("read")
            hiding_abstract = ", ".join(abstract_tokens)
            lines.append(f"RegisterAbs() = (ReadersAbs() ||| WritersAbs()) \\{{{hiding_abstract}}};")
            lines.append("")
            
            # Properties
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Register() refines RegisterAbs();")
            lines.append("#assert RegisterAbs() refines Register();")

            processed_code = "\n".join(lines)
            
    elif algo_id == "multi_register_mr":
        try:
            var_register, var_reader, implementation_type = re.split(r'[,\s]+', var_value.strip())
            var_register = int(var_register)
            var_reader = int(var_reader)
            implementation_type = implementation_type.lower()
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (var_register < 3) or (var_reader < 1) or (implementation_type not in ['faulty', 'correct']):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        if implementation_type == 'correct':
            lines = []
            # The number of readers (N) is given by var_reader.
            lines.append(f"#define N {var_reader};")
            lines.append("")
            
            # Shared binary array B of size var_register:
            # It is an array of length var_register with all entries 0 except the last one is 1.
            b_elements = ["0"] * (var_register - 1) + ["1"]
            b_array = "[" + ",".join(b_elements) + "]"
            lines.append("//shared binary array of size N")
            lines.append(f"var B = {b_array};")
            
            # Register value for the abstract model is R = var_register - 1
            lines.append("//register value used by the abstract model")
            lines.append(f"var R = {var_register - 1};")
            
            # Temporary array M of size N (number of readers)
            lines.append("//temporary value for abstract reader to stored the value read from register")
            lines.append("var M[N];")
            lines.append("")
            
            # Concrete Implementation Model
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            lines.append("Readers(id) = read_inv.id -> UpScan(0, id);")
            lines.append("UpScan(i, id) =  if(B[i] == 1) { DownScan(i - 1, i, id) } else { UpScan(i + 1, id) };")
            lines.append("DownScan(i, v, id) =")
            lines.append("\tif(i >= 0) {")
            lines.append("\t\tif(B[i] == 1) { DownScan(i - 1, i, id) } else { DownScan(i - 1, v, id) }")
            lines.append("\t} else {")
            lines.append("\t\tread_res.id.v -> Readers(id)")
            lines.append("\t};")
            lines.append("")
            lines.append("Writer(i) = write_inv.i -> tau{B[i] = 1;} -> WriterDownScan(i-1);")
            lines.append("WriterDownScan(i) = if(i >= 0 ) { tau{B[i] = 0;} -> WriterDownScan(i-1) } else { write_res -> Skip } ;")
            lines.append("")
            
            # Generate Writers: Writer(0)[]Writer(1)...[]Writer(var_register-1)
            writers = "[]".join(f"Writer({i})" for i in range(var_register))
            lines.append(f"Writers() = ({writers}); Writers();")
            lines.append("Register() = (|||x:{0..N-1}@Readers(x)) ||| Writers();")
            lines.append("")
            
            # Abstract Specification Model
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("ReadersAbs(id) = read_inv.id -> tau{M[id]=R;} -> read_res.id.M[id] -> ReadersAbs(id);")
            lines.append("")
            lines.append("WriterAbs(i) = write_inv.i -> tau{R=i;} -> write_res -> Skip;")
            # Generate WritersAbs similarly:
            writer_abs = "[]".join(f"WriterAbs({i})" for i in range(var_register))
            lines.append(f"WritersAbs() = ({writer_abs}); WritersAbs();")
            lines.append("RegisterAbs() = (|||x:{0..N-1}@ReadersAbs(x))||| WritersAbs();")
            lines.append("")
            
            # Properties
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Register() refines RegisterAbs();")
            lines.append("#assert RegisterAbs() refines Register();")

            processed_code = "\n".join(lines)

        else:
            lines = []
            # The number of readers is given by var_reader; N is defined using var_reader.
            lines.append(f"#define N {var_reader};")
            lines.append("")
            
            # Shared binary array: an array of length var_register with (var_register-1) zeros followed by a 1.
            lines.append("//shared binary array of size N")
            b_array = "[" + ",".join(["0"] * (var_register - 1) + ["1"]) + "]"
            lines.append(f"var B = {b_array};")
            
            # Register value for the abstract model (R) equals var_register - 1.
            lines.append("//register value used by the abstract model")
            lines.append(f"var R = {var_register - 1};")
            
            # Temporary storage for each reader (an array of size N)
            lines.append("//temporary value for abstract reader to stored the value read from register")
            lines.append("var M[N];")
            lines.append("")
            
            # Concrete Implementation Model
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            lines.append("Readers(id) = read_inv.id -> UpScan(0, id);")
            lines.append("UpScan(i, id) =  if(B[i] == 1) { read_res.id.i -> Readers(id) } else { UpScan(i + 1, id) };")
            lines.append("")
            lines.append("Writer(i) = write_inv.i -> tau{B[i] = 1;} -> WriterDownScan(i-1);")
            lines.append("WriterDownScan(i) = if(i >= 0 ) { tau{B[i] = 0;} -> WriterDownScan(i-1) } else { write_res -> Skip } ;")
            lines.append("")
            
            # Compose the Writers: a choice of Writer processes for each page from 0 to var_register-1.
            writer_items = [f"Writer({i})" for i in range(var_register)]
            writers_str = "[]".join(writer_items)
            lines.append(f"Writers() = ({writers_str}); Writers();")
            lines.append("Register() = (|||x:{0..N-1}@Readers(x)) ||| Writers();")
            
            # Abstract Specification Model
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("ReadersAbs(id) = read_inv.id -> tau{M[id]=R;} -> read_res.id.M[id] -> ReadersAbs(id);")
            lines.append("")
            lines.append("WriterAbs(i) = write_inv.i -> tau{R=i;} -> write_res -> Skip;")
            writer_abs_items = [f"WriterAbs({i})" for i in range(var_register)]
            writers_abs_str = "[]".join(writer_abs_items)
            lines.append(f"WritersAbs() = ({writers_abs_str}); WritersAbs();")
            lines.append("RegisterAbs() = (|||x:{0..N-1}@ReadersAbs(x))||| WritersAbs();")
            lines.append("")
            
            # Properties
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Register() refines RegisterAbs();")
            lines.append("#assert RegisterAbs() refines Register();")

            processed_code = "\n".join(lines)

    elif algo_id == "concurrent_stack":
        try:
            num_process, stack_length, event_type = re.split(r'[,\s]+', var_value.strip())
            num_process = int(num_process)
            stack_length = int(stack_length)
            event_type = event_type.lower()
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_process < 2) or (stack_length < 1) or (event_type not in ['tau', 'explicit']):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        if event_type == 'tau':
            lines = []
            # Header comments and macro definitions.
            lines.append("////number of processes")
            lines.append(f"#define N {num_process};")
            lines.append("//stack size")
            lines.append(f"#define SIZE {stack_length};")
            lines.append("")
            
            # Shared variables for the concrete implementation.
            lines.append("//shared head pointer for the concrete implementation")
            lines.append("var H = 0;")
            lines.append("//local variable to store the temporary head value")
            lines.append("var HL[N];")
            lines.append("")
            
            # Shared variables for the abstract implementation.
            lines.append("//shared head pointer for the abstract implementation")
            lines.append("var HA = 0;")
            lines.append("//local variable to store the temporary head value")
            lines.append("var HLA[N];")
            lines.append("")
            
            # Concrete Implementation Model.
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            
            # PushLoop procedure – using indentation as in the samples.
            lines.append("PushLoop(i) = tau{HL[i]=H;} -> (")
            lines.append("\tifa (HL[i] == H) {")
            lines.append("\t\ttau{if(H < SIZE) {H = H+1;} HL[i]=H;} -> tau -> push_res.i.HL[i] -> Skip")
            lines.append("\t} else {")
            lines.append("\t\tPushLoop(i)")
            lines.append("\t});")
            lines.append("")
            
            # PopLoop procedure.
            lines.append("PopLoop(i) = tau{HL[i]=H;} -> ")
            lines.append("\t(if(HL[i] == 0) {")
            lines.append("\t\tpop_res.i.0 -> Skip ")
            lines.append("\t} else {")
            lines.append("\t\t(ifa(HL[i] != H) { PopLoop(i) } else { tau{H = H-1; HL[i]=H;} -> tau -> pop_res.i.(HL[i]+1) -> Skip")
            lines.append("\t\t})")
            lines.append("\t});")
            lines.append("")
            
            # Process and Stack definitions.
            lines.append("Process(i) = (push_inv.i -> PushLoop(i)[] pop_inv.i -> PopLoop(i));Process(i);")
            lines.append("Stack() = |||x:{0..N-1}@Process(x);")
            
            # Abstract Specification Model.
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("PushAbs(i) = push_inv.i -> tau{if(HA < SIZE) {HA = HA+1;}; HLA[i]=HA;} -> push_res.i.HLA[i] -> Skip;")
            lines.append("")
            lines.append("PopAbs(i) = pop_inv.i ->")
            lines.append("\t(ifa(HA == 0) {")
            lines.append("\t\ttau-> pop_res.i.0 -> Skip ")
            lines.append("\t} else {")
            lines.append("\t\t tau{HA = HA -1; HLA[i]=HA;} -> pop_res.i.(HLA[i]+1) -> Skip")
            lines.append("\t});")
            lines.append("")
            lines.append("ProcessAbs(i) = (PushAbs(i)[]PopAbs(i));ProcessAbs(i);")
            lines.append("")
            lines.append("StackAbs() = |||x:{0..N-1}@ProcessAbs(x);")
            
            # Properties.
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Stack() refines StackAbs();")
            lines.append("#assert StackAbs() refines Stack();")

            processed_code = "\n".join(lines)
        else: # explicit
            lines = []
            # Header macros
            lines.append("////number of processes")
            lines.append(f"#define N {num_process};")
            lines.append("//stack size")
            lines.append(f"#define SIZE {stack_length};")
            lines.append("")
            
            # Shared variables for the concrete implementation.
            lines.append("//shared head pointer for the concrete implementation")
            lines.append("var H = 0;")
            lines.append("//local variable to store the temporary head value")
            lines.append("var HL[N];")
            lines.append("")
            
            # Shared variables for the abstract implementation.
            lines.append("//shared head pointer for the abstract implementation")
            lines.append("var HA = 0;")
            lines.append("//local variable to store the temporary head value")
            lines.append("var HLA[N];")
            lines.append("")
            
            # Concrete Implementation Model
            lines.append("////////////////The Concrete Implementation Model//////////////////")
            lines.append("PushLoop(i) = headread.i{HL[i]=H;} -> (")
            lines.append("\tifa (HL[i] == H) {")
            lines.append("\t\tpush.i{if(H < SIZE) {H = H+1;} HL[i]=H;} -> tau -> push_res.i.HL[i] -> Skip")
            lines.append("\t} else {")
            lines.append("\t\tPushLoop(i)")
            lines.append("\t});")
            lines.append("")
            lines.append("PopLoop(i) = headread.i{HL[i]=H;} -> ")
            lines.append("\t(if(HL[i] == 0) {")
            lines.append("\t\tpop_res.i.0 -> Skip ")
            lines.append("\t} else {")
            lines.append("\t\t(ifa(HL[i] != H) { PopLoop(i) } else { pop.i{H = H-1; HL[i]=H;} -> tau -> pop_res.i.(HL[i]+1) -> Skip")
            lines.append("\t\t})")
            lines.append("\t});")
            lines.append("")
            lines.append("Process(i) = (push_inv.i -> PushLoop(i)[] pop_inv.i -> PopLoop(i));Process(i);")
            
            # For the concrete model, build the hiding set tokens.
            concrete_tokens = []
            for i in range(num_process):
                concrete_tokens.append(f"headread.{i}")
                concrete_tokens.append(f"push.{i}")
                concrete_tokens.append(f"pop.{i}")
            concrete_hiding = ", ".join(concrete_tokens)
            lines.append(f"Stack() = (|||x:{{0..N-1}}@Process(x)) \\ {{{concrete_hiding}}};")
            lines.append("")
            
            # Abstract Specification Model
            lines.append("////////////////The Abstract Specification Model//////////////////")
            lines.append("PushAbs(i) = push_inv.i -> push.i{if(HA < SIZE) {HA = HA+1;}; HLA[i]=HA;} -> push_res.i.HLA[i] -> Skip;")
            lines.append("")
            lines.append("PopAbs(i) = pop_inv.i ->")
            lines.append("\t(ifa(HA == 0) {")
            lines.append("\t\ttau-> pop_res.i.0 -> Skip ")
            lines.append("\t} else {")
            lines.append("\t\t pop_empty.i{HA = HA -1; HLA[i]=HA;} -> pop_res.i.(HLA[i]+1) -> Skip")
            lines.append("\t});")
            lines.append("")
            lines.append("ProcessAbs(i) = (PushAbs(i)[]PopAbs(i));ProcessAbs(i);")
            
            # For the abstract model, build the hiding set tokens.
            abstract_tokens = []
            for i in range(num_process):
                abstract_tokens.append(f"push.{i}")
                abstract_tokens.append(f"pop.{i}")
                abstract_tokens.append(f"pop_empty.{i}")
            abstract_hiding = ", ".join(abstract_tokens)
            lines.append(f"StackAbs() = (|||x:{{0..N-1}}@ProcessAbs(x)) \\ {{{abstract_hiding}}};")
            lines.append("")
            
            # Properties
            lines.append("////////////////The Properties//////////////////")
            lines.append("#assert Stack() refines StackAbs();")
            lines.append("#assert StackAbs() refines Stack();")
            
            processed_code = "\n".join(lines)

    elif algo_id == "concurrent_stack_linear":
        try:
            num_process, stack_length = re.split(r'[,\s]+', var_value.strip())
            num_process = int(num_process)
            stack_length = int(stack_length)
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the two variables, and separated the values by comma or space!")
        if (num_process < 2) or (stack_length < 1):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        lines = []
        # Header macros.
        lines.append("////number of processes")
        lines.append(f"#define N {num_process};")
        lines.append("//stack size")
        lines.append(f"#define SIZE {stack_length};")
        lines.append("")
        
        # Shared variables.
        lines.append("//shared head pointer for the concrete implementation")
        lines.append("var H = 0;")
        lines.append("//local variable to store the temporary head value")
        lines.append("var HL[N];")
        lines.append("//shared head pointer for the abstract implementation")
        lines.append("var HA = 0;")
        lines.append("")
        
        # Concrete Implementation Model.
        lines.append("////////////////The Concrete Implementation Model//////////////////")
        lines.append("Push(i) = ")
        lines.append("\t    tau{HL[i]=H;} -> ")
        lines.append("\t    ifa (HL[i] == H) {")
        lines.append("\t\t    push.i.(H+1){if(H < SIZE) {H = H+1;}} -> Skip")
        lines.append("\t    } else {")
        lines.append("\t\t    tau -> Push(i)")
        lines.append("\t 	};")
        lines.append("")
        lines.append("Pop(i) =")
        lines.append("\t\t    tau{HL[i]=H;} -> ")
        lines.append("\t\t    ifa(H == 0) {")
        lines.append("\t\t\t    pop.i.0 -> Skip ")
        lines.append("\t\t    } else {")
        lines.append("\t\t\t    tau-> ifa(HL[i] != H) {tau -> Pop(i) } else {pop.i.H{if(H > 0) {H = H -1;}} -> Skip")
        lines.append("\t\t\t    }")
        lines.append("\t\t    };")
        lines.append("")
        lines.append("Process(i) = (Push(i)[]Pop(i));Process(i);")
        lines.append("Stack() = (|||x:{0..N-1}@Process(x));")
        lines.append("")
        
        # Abstract Specification Model.
        lines.append("////////////////The Abstract Specification Model//////////////////")
        lines.append("PushAbs(i) = push.i.(HA + 1) {if(HA < SIZE) {HA = HA+1;}} -> Skip;")
        lines.append("PopAbs(i) = pop.i.HA{if(HA > 0) {HA = HA -1;}} -> Skip;")
        lines.append("")
        lines.append("ProcessAbs(i) = (PushAbs(i)[]PopAbs(i));ProcessAbs(i);")
        lines.append("")
        lines.append("StackAbs() = (|||x:{0..N-1}@ProcessAbs(x));")
        lines.append("")
        
        # Properties.
        lines.append("////////////////The Properties//////////////////")
        lines.append("#assert Stack() refines StackAbs();")
        lines.append("#assert StackAbs() refines Stack();")

        processed_code = "\n".join(lines)

    elif algo_id == "mailbox":
        try:
            var_value, implementation_type, optimization_type = re.split(r'[,\s]+', var_value.strip())
            var_value = int(var_value)
            implementation_type = implementation_type.lower()
            optimization_type = optimization_type.lower()
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (var_value < 2) or (implementation_type not in ['waitfree', 'non_blocking']) or (optimization_type not in ['no_optimization', 'with_optimization']):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        if implementation_type == 'non_blocking' and optimization_type == 'no_optimization':
            ROUND = 2 * var_value
            MaxROUND = var_value
            # Use a raw f-string (triple-quoted) with proper doubling of curly braces where needed.
            processed_code = f'''#import "PAT.Lib.Example";

#define EQ 0;
#define NEQ 1;
 
#define BOTTOM  0;
#define UNKNOWN  1;
#define SUCCESS  2;
#define DONE  3;
 
//bounded number of Rounds
#define ROUND {ROUND};
#define MaxROUND {MaxROUND};
 
var A0TS[ROUND];
var A0C[ROUND];
 
var A1TS[ROUND];
var A1C[ROUND];
 
var B0[ROUND];
var B1[ROUND];
 
var TS = [1, 1];
var Rel = [0, 0];
 
var Counter[2];
var Rounds[2];
var Otherc[2];
var OutvalueTS[2];
var OutvalueC[2];
var Outcome[2];
var TSL[2];
var RelL[2];
 
var NextTS=[2,2];
var Otherts = [1,1];
var TSC = [1, 1];
 
var rnd0 = 0;
var rnd1 = 0;
 
////////////////The Concrete Implementation Model//////////////////
//process 0: postman
Postman(i) = [i < MaxROUND](deliver_inv -> tau{{Counter[0] = Counter[0] + 1;}} -> (Compare(0); deliver_res -> Postman(i+1)));
 
Compare(i) = tau{{Outcome[i] = UNKNOWN;}} -> 
   (CompareLoop(i); 
    (if(Counter[i]!=Otherc[i]) {{
         tau{{TS[i] = TSC[i]; Rel[i] = NEQ;}} -> Skip
     }} else {{ 
         tau{{TS[i] = TSC[i]; Rel[i] = EQ;}} -> Skip
     }})
   );
 
CompareLoop(i)  =  if (Outcome[i] == SUCCESS) {{ Skip }} else {{
                  tau{{Rounds[i] = Rounds[i]+1;}} -> tau{{TSC[i] = NextTS[i];}} -> Sussus(i);
                        (if(OutvalueC[i] !=  BOTTOM) {{ 
                             tau{{Otherts[i] = OutvalueTS[i];}} -> tau{{Otherc[i] = OutvalueC[i];}} -> Skip
                        }} else {{
                             Skip
                        }});
                        tau{{NextTS[i] = call(dominate, Otherts[i], TS[1-i]);}} -> CompareLoop(i)
                  }};
 
Sussus(i) = if(i==0) {{ Sussus0() }} else {{ Sussus1()}};
 
Sussus0() = tau{{rnd0 = Rounds[0] - 1; A0TS[rnd0] = TSC[0]; A0C[rnd0] = Counter[0];}} ->  tau{{OutvalueTS[0] = A1TS[rnd0]; OutvalueC[0] = A1C[rnd0];}} ->
    (if(OutvalueC[0] == BOTTOM ) {{
        tau{{Outcome[0] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B0[rnd0] = DONE;}} ->
            (if(B1[rnd0] == BOTTOM) {{
                tau{{Outcome[0] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[0] = SUCCESS;}} -> Skip
             }})
    }});
 
Sussus1() = tau{{rnd1 = Rounds[1] - 1; A1TS[rnd1] = TSC[1]; A1C[rnd1] = Counter[1];}} ->  tau{{OutvalueTS[1] = A0TS[rnd1]; OutvalueC[1] = A0C[rnd1];}} ->
    (if(OutvalueTS[1] == BOTTOM ) {{
        tau{{Outcome[1] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B1[rnd1] = DONE;}} ->
            (if(B0[rnd1] == BOTTOM) {{
                tau{{Outcome[1] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[1] = SUCCESS;}} -> Skip
             }})
    }});
 
//process 1: wife
Check() = check_inv -> tau{{TSL[0] = TS[0]; RelL[0] = Rel[0];}} -> tau{{TSL[1] = TS[1]; RelL[1] = Rel[1];}} ->
   (if(call(mailorder, TSL[0],  TSL[1])) {{
           (if(RelL[0] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }}) 
    }} else {{
           (if(RelL[1] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }})
    }});
  
Remove() = remove_inv -> tau{{Counter[1] = Counter[1] + 1;}} -> (Compare(1); remove_res -> Skip);
Wife(i) = [i < MaxROUND](Check();Wife(i+1));
Mailbox() = Postman(0) ||| Wife(0);
 
////////////////The Abstract Specification Model////////////////// 
var FlagL = 0;
var CountA = 0;
 
PostmanAbs(i) = [i < MaxROUND]( deliver_inv -> deliver{{CountA = CountA + 1;}} -> deliver_res -> PostmanAbs(i+1));
 
CheckAbs() = check_inv -> check{{FlagL = CountA;}} -> (if(FlagL > 0) {{check_rest -> RemoveAbs()}} else {{ check_resf -> CheckAbs() }});
RemoveAbs() = remove_inv -> remove{{CountA = CountA - 1;}} -> remove_res -> Skip;
WifeAbs(i) = [i < MaxROUND] (CheckAbs();WifeAbs(i+1));
 
MailboxAbs() = (PostmanAbs(0) ||| WifeAbs(0)) \{{deliver, check, remove}};
 
////////////////The Properties//////////////////
#assert Mailbox() refines MailboxAbs();
#assert MailboxAbs() refines Mailbox();
'''
            
        elif implementation_type == 'non_blocking' and optimization_type == 'with_optimization':
            ROUND = 2 * var_value
            MaxROUND = var_value
            code = r'''#import "PAT.Lib.Example";

#define EQ 0;
#define NEQ 1;
 
#define BOTTOM  0;
#define UNKNOWN  1;
#define SUCCESS  2;
#define DONE  3;
 
//bounded number of Rounds
#define ROUND {ROUND};
#define MaxROUND {MaxROUND};
 
var A0TS[ROUND];
var A0C[ROUND];
 
var A1TS[ROUND];
var A1C[ROUND];
 
var B0[ROUND];
var B1[ROUND];
 
var TS = [1, 1];
var Rel = [0, 0];
 
var Counter[2];
var Rounds[2];
var Otherc[2];
var OutvalueTS[2];
var OutvalueC[2];
var Outcome[2];
var TSL[2];
var RelL[2];
 
var NextTS=[2,2];
var Otherts = [1,1];
var TSC = [1, 1];
 
var rnd0 = 0;
var rnd1 = 0;
 
////////////////The Concrete Implementation Model//////////////////
//process 0: postman
Postman(i) = [i < MaxROUND](deliver_inv -> tau{{Counter[0] = Counter[0] + 1;}} -> (Compare(0); deliver_res -> Postman(i+1)));
 
Compare(i) = tau{{Outcome[i] = UNKNOWN;}} -> 
   (CompareLoop(i); 
    (if(Counter[i]!=Otherc[i]) {{
         tau{{TS[i] = TSC[i]; Rel[i] = NEQ;}} -> Skip
     }} else {{ 
         tau{{TS[i] = TSC[i]; Rel[i] = EQ;}} -> Skip
     }})
   );
 
var TRound[2];
var TOtherRound[2];
CompareLoop(i)  =  if (Outcome[i] == SUCCESS) {{ Skip }} else {{
                  tau{{TOtherRound[i] = Rounds[1-i];}} -> tau{{ if(Rounds[i]+1 > TOtherRound[i]-1) {{ TRound[i] = Rounds[i]+1;}} else {{TRound[i] = TOtherRound[i]-1;}} }} -> tau{{Rounds[i] = TRound[i];}} -> tau{{TSC[i] = NextTS[i];}} -> Sussus(i);
                        (if(OutvalueC[i] !=  BOTTOM) {{ 
                             tau{{Otherts[i] = OutvalueTS[i];}} -> tau{{Otherc[i] = OutvalueC[i];}} -> Skip
                        }} else {{
                             Skip
                        }});
                        tau{{NextTS[i] = call(dominate, Otherts[i], TS[1-i]);}} -> CompareLoop(i)
                  }};
 
Sussus(i) = if(i==0) {{ Sussus0() }} else {{ Sussus1()}};
 
Sussus0() = tau{{rnd0 = Rounds[0] - 1; A0TS[rnd0] = TSC[0]; A0C[rnd0] = Counter[0];}} ->  tau{{OutvalueTS[0] = A1TS[rnd0]; OutvalueC[0] = A1C[rnd0];}} ->
    (if(OutvalueC[0] == BOTTOM ) {{
        tau{{Outcome[0] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B0[rnd0] = DONE;}} ->
            (if(B1[rnd0] == BOTTOM) {{
                tau{{Outcome[0] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[0] = SUCCESS;}} -> Skip
             }})
    }});
 
Sussus1() = tau{{rnd1 = Rounds[1] - 1; A1TS[rnd1] = TSC[1]; A1C[rnd1] = Counter[1];}} ->  tau{{OutvalueTS[1] = A0TS[rnd1]; OutvalueC[1] = A0C[rnd1];}} ->
    (if(OutvalueTS[1] == BOTTOM ) {{
        tau{{Outcome[1] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B1[rnd1] = DONE;}} ->
            (if(B0[rnd1] == BOTTOM) {{
                tau{{Outcome[1] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[1] = SUCCESS;}} -> Skip
             }})
    }});
 
//process 1: wife
Check() = check_inv -> tau{{TSL[0] = TS[0]; RelL[0] = Rel[0];}} -> tau{{TSL[1] = TS[1]; RelL[1] = Rel[1];}} ->
   (if(call(mailorder, TSL[0],  TSL[1])) {{
           (if(RelL[0] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }}) 
    }} else {{
           (if(RelL[1] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }})
    }}); 
  
  
Remove() = remove_inv -> tau{{Counter[1] = Counter[1] + 1;}} -> (Compare(1); remove_res -> Skip);
Wife(i) = [i < MaxROUND](Check();Wife(i+1));
Mailbox() = Postman(0) ||| Wife(0);
 
////////////////The Abstract Specification Model////////////////// 
var FlagL = 0;
var CountA = 0;
 
PostmanAbs(i) = [i < MaxROUND]( deliver_inv -> deliver{{CountA = CountA + 1;}} -> deliver_res -> PostmanAbs(i+1));
 
CheckAbs() = check_inv -> check{{FlagL = CountA;}} -> (if(FlagL > 0) {{check_rest -> RemoveAbs()}} else {{ check_resf -> CheckAbs() }});
RemoveAbs() = remove_inv -> remove{{CountA = CountA - 1;}} -> remove_res -> Skip;
WifeAbs(i) = [i < MaxROUND] (CheckAbs();WifeAbs(i+1));
 
MailboxAbs() = (PostmanAbs(0) ||| WifeAbs(0)) \{{deliver, check, remove}};
 
////////////////The Properties//////////////////
#assert Mailbox() refines MailboxAbs();
#assert MailboxAbs() refines Mailbox();
'''

            processed_code = code.format(ROUND=ROUND, MaxROUND=MaxROUND)

        elif implementation_type == 'waitfree' and optimization_type == 'no_optimization':
            ROUND = 2 * var_value
            MaxROUND = var_value
            processed_code = f'''#import "PAT.Lib.Example";

#define EQ 0;
#define NEQ 1;
 
#define BOTTOM  0;
#define UNKNOWN  1;
#define SUCCESS  2;
#define DONE  3;
 
//bounded number of Rounds
#define ROUND {ROUND};
#define MaxROUND {MaxROUND};
 
var A0TS[ROUND];
var A0C[ROUND];
 
var A1TS[ROUND];
var A1C[ROUND];
 
var B0[ROUND];
var B1[ROUND];
 
var TS = [1, 1];
var Rel = [0, 0];
 
var Counter[2];
var Rounds[2];
var Otherc[2];
var OutvalueTS[2];
var OutvalueC[2];
var Outcome[2];
var TSL[2];
var RelL[2];
 
var NextTS=[2,2];
var Otherts = [1,1];
var TSC = [1, 1];
 
var rnd0 = 0;
var rnd1 = 0;
 
////////////////The Concrete Implementation Model//////////////////
//process 0: postman
Postman(i) = [i < MaxROUND](deliver_inv -> tau{{Counter[0] = Counter[0] + 1;}} -> (Compare(0); deliver_res -> Postman(i+1)));
 
Compare(i) = tau{{Outcome[i] = UNKNOWN;}} -> 
   (CompareLoop(i); 
    (if(Counter[i]!=Otherc[i]) {{
         tau{{TS[i] = TSC[i]; Rel[i] = NEQ;}} -> Skip
     }} else {{ 
         tau{{TS[i] = TSC[i]; Rel[i] = EQ;}} -> Skip
     }})
   );
 
CompareLoop(i)  =  if (Outcome[i] == SUCCESS) {{ Skip }} else {{
              if(i == 1 && Counter[i] < Otherc[i]) {{ 
                  Skip 
              }} else {{
                  tau{{Rounds[i] = Rounds[i]+1;}} -> tau{{TSC[i] = NextTS[i];}} -> Sussus(i);
                        (if (OutvalueC[i] !=  BOTTOM) {{ 
                             tau{{Otherts[i] = OutvalueTS[i];}} -> tau{{Otherc[i] = OutvalueC[i];}} -> Skip
                        	}} else {{
                             Skip
                         }});
                         tau{{NextTS[i] = call(dominate, Otherts[i], TS[1-i]);}} -> CompareLoop(i)
              }}}};
 
Sussus(i) = if(i==0) {{ Sussus0() }} else {{ Sussus1()}};
 
Sussus0() = tau{{rnd0 = Rounds[0] - 1; A0TS[rnd0] = TSC[0]; A0C[rnd0] = Counter[0];}} ->  tau{{OutvalueTS[0] = A1TS[rnd0]; OutvalueC[0] = A1C[rnd0];}} ->
    (if(OutvalueC[0] == BOTTOM ) {{
        tau{{Outcome[0] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B0[rnd0] = DONE;}} ->
            (if(B1[rnd0] == BOTTOM) {{
                tau{{Outcome[0] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[0] = SUCCESS;}} -> Skip
             }})
    }});
 
Sussus1() = tau{{rnd1 = Rounds[1] - 1; A1TS[rnd1] = TSC[1]; A1C[rnd1] = Counter[1];}} ->  tau{{OutvalueTS[1] = A0TS[rnd1]; OutvalueC[1] = A0C[rnd1];}} ->
    (if(OutvalueTS[1] == BOTTOM ) {{
        tau{{Outcome[1] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B1[rnd1] = DONE;}} ->
            (if(B0[rnd1] == BOTTOM) {{
                tau{{Outcome[1] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[1] = SUCCESS;}} -> Skip
             }})
    }});
 
//process 1: wife
Check() = check_inv -> tau{{TSL[0] = TS[0]; RelL[0] = Rel[0];}} -> tau{{TSL[1] = TS[1]; RelL[1] = Rel[1];}} ->
   (if(call(mailorder, TSL[0],  TSL[1])) {{
           (if(RelL[0] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }}) 
    }} else {{
           (if(RelL[1] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }})
    }}); 
  
Remove() = remove_inv -> tau{{Counter[1] = Counter[1] + 1;}} -> (Compare(1); remove_res -> Skip);
Wife(i) = [i < MaxROUND](Check();Wife(i+1));
Mailbox() = Postman(0) ||| Wife(0);
 
////////////////The Abstract Specification Model////////////////// 
var FlagL = 0;
var CountA = 0;
 
PostmanAbs(i) =[i < MaxROUND]( deliver_inv -> deliver{{CountA = CountA + 1;}} -> deliver_res -> PostmanAbs(i+1));
 
CheckAbs() = check_inv -> check{{FlagL = CountA;}} -> (if(FlagL > 0) {{check_rest -> RemoveAbs()}} else {{ check_resf -> CheckAbs() }});
RemoveAbs() = remove_inv -> remove{{CountA = CountA - 1;}} -> remove_res -> Skip;
WifeAbs(i) = [i < MaxROUND] (CheckAbs();WifeAbs(i+1));
 
MailboxAbs() = (PostmanAbs(0) ||| WifeAbs(0)) \{{deliver, check, remove}};
 
////////////////The Properties//////////////////
#assert Mailbox() refines MailboxAbs();
#assert MailboxAbs() refines Mailbox();
'''

        else: # waitfree & with_optimization
            ROUND = 2 * var_value
            MaxROUND = var_value
            processed_code = f'''#import "PAT.Lib.Example";

#define EQ 0;
#define NEQ 1;
 
#define BOTTOM  0;
#define UNKNOWN  1;
#define SUCCESS  2;
#define DONE  3;
 
//bounded number of Rounds
#define ROUND {ROUND};
#define MaxROUND {MaxROUND};
 
var A0TS[ROUND];
var A0C[ROUND];
 
var A1TS[ROUND];
var A1C[ROUND];
 
var B0[ROUND];
var B1[ROUND];
 
var TS = [1, 1];
var Rel = [0, 0];
 
var Counter[2];
var Rounds[2];
var Otherc[2];
var OutvalueTS[2];
var OutvalueC[2];
var Outcome[2];
var TSL[2];
var RelL[2];
 
var NextTS=[2,2];
var Otherts = [1,1];
var TSC = [1, 1];
 
var rnd0 = 0;
var rnd1 = 0;
 
////////////////The Concrete Implementation Model//////////////////
//process 0: postman
Postman(i) = [i < MaxROUND](deliver_inv -> tau{{Counter[0] = Counter[0] + 1;}} -> (Compare(0); deliver_res -> Postman(i+1)));
 
Compare(i) = tau{{Outcome[i] = UNKNOWN;}} -> 
   (CompareLoop(i); 
    (if(Counter[i]!=Otherc[i]) {{
         tau{{TS[i] = TSC[i]; Rel[i] = NEQ;}} -> Skip
     }} else {{ 
         tau{{TS[i] = TSC[i]; Rel[i] = EQ;}} -> Skip
     }})
   );
 
var TRound[2];
var TOtherRound[2];
CompareLoop(i)  =  if (Outcome[i] == SUCCESS) {{ Skip }} else {{
              if(i == 1 && Counter[i] < Otherc[i]) {{ 
                  Skip 
              }} else {{
                  tau{{TOtherRound[i] = Rounds[1-i];}} -> tau{{ if(Rounds[i]+1 > TOtherRound[i]-1) {{ TRound[i] = Rounds[i]+1;}} else {{TRound[i] = TOtherRound[i]-1;}} }} -> tau{{Rounds[i] = TRound[i];}} -> tau{{TSC[i] = NextTS[i];}} -> Sussus(i);
                        (if (OutvalueC[i] !=  BOTTOM) {{ 
                             tau{{Otherts[i] = OutvalueTS[i];}} -> tau{{Otherc[i] = OutvalueC[i];}} -> Skip
                        	}} else {{
                             Skip
                         }});
                         tau{{NextTS[i] = call(dominate, Otherts[i], TS[1-i]);}} -> CompareLoop(i)
              }}}};
 
Sussus(i) = if(i==0) {{ Sussus0() }} else {{ Sussus1()}};
 
Sussus0() = tau{{rnd0 = Rounds[0] - 1; A0TS[rnd0] = TSC[0]; A0C[rnd0] = Counter[0];}} ->  tau{{OutvalueTS[0] = A1TS[rnd0]; OutvalueC[0] = A1C[rnd0];}} ->
    (if(OutvalueC[0] == BOTTOM ) {{
        tau{{Outcome[0] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B0[rnd0] = DONE;}} ->
            (if(B1[rnd0] == BOTTOM) {{
                tau{{Outcome[0] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[0] = SUCCESS;}} -> Skip
             }})
    }});
 
Sussus1() = tau{{rnd1 = Rounds[1] - 1; A1TS[rnd1] = TSC[1]; A1C[rnd1] = Counter[1];}} ->  tau{{OutvalueTS[1] = A0TS[rnd1]; OutvalueC[1] = A0C[rnd1];}} ->
    (if(OutvalueTS[1] == BOTTOM ) {{
        tau{{Outcome[1] = SUCCESS;}} -> Skip
    }} else {{
        tau{{B1[rnd1] = DONE;}} ->
            (if(B0[rnd1] == BOTTOM) {{
                tau{{Outcome[1] = UNKNOWN;}} -> Skip
             }} else {{
                tau{{Outcome[1] = SUCCESS;}} -> Skip
             }})
    }});
 
//process 1: wife
Check() = check_inv -> tau{{TSL[0] = TS[0]; RelL[0] = Rel[0];}} -> tau{{TSL[1] = TS[1]; RelL[1] = Rel[1];}} ->
   (if(call(mailorder, TSL[0],  TSL[1])) {{
           (if(RelL[0] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }}) 
    }} else {{
           (if(RelL[1] == EQ) {{
               check_resf -> Check()
           }} else {{
               check_rest -> Remove()
           }})
    }}); 
  
Remove() = remove_inv -> tau{{Counter[1] = Counter[1] + 1;}} -> (Compare(1); remove_res -> Skip);
Wife(i) = [i < MaxROUND](Check();Wife(i+1));
Mailbox() = Postman(0) ||| Wife(0);
 
////////////////The Abstract Specification Model////////////////// 
var FlagL = 0;
var CountA = 0;
 
PostmanAbs(i) =[i < MaxROUND]( deliver_inv -> deliver{{CountA = CountA + 1;}} -> deliver_res -> PostmanAbs(i+1));
 
CheckAbs() = check_inv -> check{{FlagL = CountA;}} -> (if(FlagL > 0) {{check_rest -> RemoveAbs()}} else {{ check_resf -> CheckAbs() }});
RemoveAbs() = remove_inv -> remove{{CountA = CountA - 1;}} -> remove_res -> Skip;
WifeAbs(i) = [i < MaxROUND] (CheckAbs();WifeAbs(i+1));
 
MailboxAbs() = (PostmanAbs(0) ||| WifeAbs(0)) \{{deliver, check, remove}};
 
////////////////The Properties//////////////////
#assert Mailbox() refines MailboxAbs();
#assert MailboxAbs() refines Mailbox();
'''

    elif algo_id == "snzi":
        try:
            num_processes, num_treenodes, num_operations, model_type = re.split(r'[,\s]+', var_value.strip())
            num_processes = int(num_processes)
            num_treenodes = int(num_treenodes)
            num_operations = int(num_operations)
            model_type = model_type.lower()
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_processes < 2) or (num_treenodes < 1) or (num_operations < 1) or (model_type not in ['detailed', 'compact']):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        if model_type == 'detailed':
            processed_code = f'''//This model is for "SNZI: Scalable NonZero Indicators"

//number of processes
#define PRO_SIZE {num_processes};

// number of nodes
#define NODE_SIZE {num_treenodes};


//------------------------------shared variable------------------------------
// Since SNZI algorithm is organized as a rooted tree of SNZI objects,
// we create a NODE_SIZE array of Node objects. The root is the first element of the array,
// and for 0 < i < NODE_SIZE, the parent of the ith node is the (i-1)/2th node.

// Array of shared variables of nodes (including hierarchical and root nodes),
// each node has its own local copy. So there are NODE_SIZE copies.
var node_c[NODE_SIZE];  // the original X.c
var node_v[NODE_SIZE];  // the original X.v

var node_a = 0;    // the original X.a for the root (i.e. the first element of the array)

// presence indicator
var I = 0;


//------------------------------local variable------------------------------
// Local variables for nodes when a process arrives at or departs from a node.
// For node i, the local variable of process j is at index (i * PRO_SIZE + j).
var cc[NODE_SIZE * PRO_SIZE];
var vv[NODE_SIZE * PRO_SIZE];

// For the root node, at most PRO_SIZE copies.
var aa[PRO_SIZE];

// Local copies for the root node representing x'
var rootc[PRO_SIZE];
var roota[PRO_SIZE];
var rootv[PRO_SIZE];

// Other local variables for hierarchical SNZI nodes:
// There are NODE_SIZE * PRO_SIZE local variables.
var succ[NODE_SIZE * PRO_SIZE];    // original succ in the Arrive operation
var undoArr[NODE_SIZE * PRO_SIZE]; // original undoArr in the Arrive operation

// For the LL-SC primitive:
var updateCounter;
var pro_counter[PRO_SIZE];


//------------------------------The Concrete Implementation Model------------------------------
// Single-entry of Arrival and Departure operations on any node:
ArriveImpl(process, node) = arrive_inv.process -> ArriveGeneral(process, node); arrive_res.process -> Skip;
DepartImpl(process, node) = depart_inv.process -> DepartGeneral(process, node); depart_res.process -> Skip;

ArriveGeneral(process, node) = ifa (node == 0) {{ArriveRoot(process)}} else {{Arrive(process, node)}};
DepartGeneral(process, node) = ifa (node == 0) {{DepartRoot(process)}} else {{Depart(process, node)}};

//------------------------------start - root node operations------------------------------
// Arrival on the root node:
ArriveRoot(process) = t {{cc[process] = node_c[0]; aa[process] = node_a; vv[process] = node_v[0];}}
                      -> Repeat(process); Until(process);

Repeat(process) = if (cc[process] == 0)
                  {{ t {{rootc[process] = 1; roota[process] = 1; rootv[process] = vv[process] + 1;}} -> Skip }}
                  else
                  {{ t {{rootc[process] = cc[process] + 1; roota[process] = aa[process]; rootv[process] = vv[process];}} -> Skip }};
Until(process) = ifa (cc[process] == node_c[0] && aa[process] == node_a && vv[process] == node_v[0])
                 {{ t {{node_c[0] = rootc[process]; node_a = roota[process]; node_v[0] = rootv[process];}} -> Write(process) }}
                 else
                 {{ ArriveRoot(process) }};

Write(process) = if (roota[process] == 1)
                {{ t {{I = 1; updateCounter = updateCounter + 1;}} -> CAS(process) }}
                else
                {{ Skip }};
CAS(process) = ifa (node_c[0] == rootc[process] && node_a == roota[process] && node_v[0] == rootv[process])
              {{ t {{node_c[0] = rootc[process]; node_a = 0; node_v[0] = rootv[process];}} -> Skip }}
              else
              {{ Skip }};

// Departure from the root node:
DepartRoot(process) = t {{cc[process] = node_c[0]; aa[process] = node_a; vv[process] = node_v[0];}}
                     -> line15(process);
line15(process) = ifa (cc[process] == node_c[0] && aa[process] == node_a && vv[process] == node_v[0])
                 {{ t {{node_c[0] = cc[process] - 1; node_a = 0; node_v[0] = vv[process];}} -> l151(process) }}
                 else
                 {{ DepartRoot(process) }};
l151(process) = if (cc[process] > 1) {{ Skip }} else {{ DepartRootLoop(process) }};
DepartRootLoop(process) = t {{pro_counter[process] = updateCounter;}}
                         -> if (vv[process] != node_v[0]) {{ Skip }}
                         else {{
                             ifa (pro_counter[process] != updateCounter)
                             {{ t -> DepartRootLoop(process) }}
                             else
                             {{ t {{I = 0; updateCounter = updateCounter + 1;}} -> Skip }}
                         }};

//------------------------------end - root node operations------------------------------


//------------------------------start - hierarchical SNZI node------------------------------
Arrive(process, node) = t {{succ[node * PRO_SIZE + process] = 0;}}
                        -> t {{undoArr[node * PRO_SIZE + process] = 0;}}
                        -> ArriveLoop1(process, node); ArriveLoop2(process, node); Skip;
ArriveLoop1(process, node) = if (succ[node * PRO_SIZE + process] == 0)
                              {{ t {{cc[node * PRO_SIZE + process] = node_c[node]; vv[node * PRO_SIZE + process] = node_v[node];}}
                                 -> ArriveCase1(process, node) }}
                              else {{ Skip }};
ArriveCase1(process, node) = if (cc[node * PRO_SIZE + process] > 1)
                              {{ l2(process, node); ArriveCase2(process, node) }}
                              else {{ ArriveCase2(process, node) }};
l2(process, node) = ifa (cc[node * PRO_SIZE + process] == node_c[node] && vv[node * PRO_SIZE + process] == node_v[node])
                    {{ t {{node_c[node] = cc[node * PRO_SIZE + process] + 2; node_v[node] = vv[node * PRO_SIZE + process];}}
                       -> t {{succ[node * PRO_SIZE + process] = 1;}} -> Skip }}
                    else {{ t -> Skip }};
ArriveCase2(process, node) = if (cc[node * PRO_SIZE + process] == 0)
                              {{ l3(process, node); ArriveCase3(process, node) }}
                              else {{ ArriveCase3(process, node) }};
l3(process, node) = ifa (cc[node * PRO_SIZE + process] == node_c[node] && vv[node * PRO_SIZE + process] == node_v[node])
                    {{ t {{node_c[node] = 1; node_v[node] = vv[node * PRO_SIZE + process] + 1;}}
                       -> t {{succ[node * PRO_SIZE + process] = 1;}}
                       -> t {{cc[node * PRO_SIZE + process] = 1; vv[node * PRO_SIZE + process] = vv[node * PRO_SIZE + process] + 1;}} -> Skip }}
                    else {{ t -> Skip }};
ArriveCase3(process, node) = if (cc[node * PRO_SIZE + process] == 1)
                              {{ ArriveGeneral(process, (node - 1)/2); l5(process, node) }}
                              else {{ ArriveLoop1(process, node) }};
l5(process, node) = ifa (cc[node * PRO_SIZE + process] == node_c[node] && vv[node * PRO_SIZE + process] == node_v[node])
                    {{ t {{node_c[node] = 2; node_v[node] = vv[node * PRO_SIZE + process];}}
                       -> ArriveLoop1(process, node) }}
                    else {{ t -> t {{undoArr[node * PRO_SIZE + process] = undoArr[node * PRO_SIZE + process] + 1;}} -> ArriveLoop1(process, node) }};
ArriveLoop2(process, node) = if (undoArr[node * PRO_SIZE + process] > 0)
                              {{ DepartGeneral(process, (node - 1)/2);
                                 t {{undoArr[node * PRO_SIZE + process] = undoArr[node * PRO_SIZE + process] - 1;}}
                                 -> ArriveLoop2(process, node) }}
                              else {{ Skip }};
Depart(process, node) = t {{cc[node * PRO_SIZE + process] = node_c[node]; vv[node * PRO_SIZE + process] = node_v[node];}}
                       -> l8(process, node); Skip;
l8(process, node) = ifa (cc[node * PRO_SIZE + process] == node_c[node] && vv[node * PRO_SIZE + process] == node_v[node])
                    {{ t {{node_c[node] = cc[node * PRO_SIZE + process] - 2; node_v[node] = vv[node * PRO_SIZE + process];}}
                       -> l9(process, node) }}
                    else {{ t -> Depart(process, node) }};
l9(process, node) = if (cc[node * PRO_SIZE + process] == 2)
                    {{ DepartGeneral(process, (node - 1)/2); Skip }}
                    else {{ Skip }};
//------------------------------end - hierarchical SNZI node------------------------------


//------------------------------Process and Query operations------------------------------
Process(i, j) = [j < {num_operations}] ( [] x:{{0..NODE_SIZE - 1}} @ (ArriveImpl(i, x); DepartImpl(i, x)); Process(i, j+1));
Query() = query.I -> Query();

SNZI() = (||| x:{{0..PRO_SIZE - 1}} @ Process(x, 0)) \\{{t}} ||| Query();


//------------------------------Abstract Specification Model------------------------------

//shared variables
var surplus = 0;
var indicator = 0;

ArriveAbs(i) = arrive_inv.i -> t{{surplus = surplus + 1; indicator = 1;}} -> arrive_res.i -> Skip;
DepartAbs(i) = depart_inv.i -> t{{surplus = surplus - 1;
                if (surplus == 0) {{indicator = 0;}}}} -> depart_res.i -> Skip;

ProcessAbs(i, j) = [j < {num_operations}] (ArriveAbs(i); DepartAbs(i); ProcessAbs(i, j+1));
QueryAbs() = query.indicator -> QueryAbs();

SNZIAbs() = (||| x:{{0..PRO_SIZE-1}} @ ProcessAbs(x, 0)) \\ {{t}} ||| QueryAbs();


#assert SNZI() refines SNZIAbs();
#assert SNZIAbs() refines SNZI();
'''
        else: # model_type is "compact"
            processed_code = f"""//This model is for SNZI:Scalable NonZero Indicators

//number of processes
#define P {num_processes};

// number of nodes
#define N {num_treenodes};


//------------------------------shared variable------------------------------

//Since SNZI algorithm is organized as a rooted tree of SNZI objects, we create a N array of Node objects.
//The root is the first element of the array,  and for 0 < i < N, the parent of the ith node is the (i-1)/2th node.

//array of shared variables of nodes (including hierarchical and root nodes),
//each nodes has its own local copy. so there are N copies 
var c[N];  //the original X.c
var v[N];  //the original X.v

var a = 0;    //the origina X.a for the root, i.e. the first element of the array

//presence indicator
var I = 0;


//------------------------------local variable------------------------------

//array of local variables which are used in the corresponding operations of nodes when a process arrives at or departs from nodes,
// i.e. representing x in the original algorithm
//as there may be N processes visiting one node concurrently, there could be N * P local variables
//this is a variant of 2-dimention array. for node i, the local variable of process j
//can be calculated by (i * P + j)
var cc[N * P];
var vv[N * P];

//aa is the local variable of root node, so there will at most P copies because only at most
//P processes can visit root node at the same time.
var aa[P];

//another local variables of root node, representing x' in the original algorithm
//As above, only at most P processes can visit the root node concurrently,
//so each array contains P elements.
var rc[P];
var ra[P];
var rv[P];

//other local variables of hierarchical SNZI node
//for each such node, P processes can visit it simultoneously,
//so the total number of each local varaible should be N * P
var s[N * P];    //the original succ in the Arrive operation 
var u[N * P];    //the original undoArr in the Arrive operation

//for LL-SC primitive
var count;
var counts[P];


//------------------------------The Concrete Implementation Model------------------------------

//Single Entry of Arrival and Departure operations on any nodes 
AI(p, n) = ai.p-> AG(p,n); ar.p -> Skip;

DI(p, n) = di.p -> DG(p,n); dr.p -> Skip;

AG(p, n) = ifa (n == 0) {{ArriveR(p)}} else {{ Arrive(p, n)}};

DG(p,n) = ifa (n == 0) {{DepartR(p)}} else {{Depart(p,n)}};

//------------------------------start - this part is for root node------------------------------
//Arrival on root node
ArriveR(p) = 	
    tau {{cc[p] = c[0]; aa[p] = a; vv[p] = v[0];}} ->// x <- Read(X)
    if (cc[p] == 0) {{ // if x.c = 0    
        tau {{rc[p] = 1; ra[p] = 1; rv[p] = vv[p] + 1;}} -> 
            Until(p); Skip //  x'<- (1, true, x.v + 1)
    }} else {{
         tau {{rc[p] = cc[p] + 1; ra[p] = aa[p]; rv[p] = vv[p];}} ->
            Until(p); Skip // x'<-(x.c+1, x.a, x.v)							
    }};

Until(p) =  
    ifa (cc[p] == c[0] && aa[p] == a && vv[p] == v[0])  //  until CAS(X, x, x')
    {{ tau {{c[0] = rc[p]; a = ra[p]; v[0] = rv[p];}} -> 
       if (ra[p] == 1) // if x'.a then
        {{ tau {{I = 1; count = count + 1;}} -> 
          ifa (c[0] == rc[p] && a == ra[p] && v[0] == rv[p])  //CAS(X,x',(x'.c, false, x'.v))
            {{ tau {{c[0] = rc[p]; a = 0; v[0] = rv[p];}} -> Skip
            }} //else {{tau  -> Skip}}
        }}
    }} else {{ tau  -> ArriveR(p)}};


//Departure from root node
DepartR(p) =  
    tau {{cc[p] = c[0]; aa[p] = a; vv[p] = v[0];}} ->
    ifa (cc[p] == c[0] && aa[p] == a && vv[p] == v[0]) //if CAS(X, x, (x.c - 1, false, x.v))
    {{ tau {{c[0] = cc[p] - 1; a = 0; v[0] = vv[p];}} -> 
      if (cc[p] > 1) {{ Skip}}  
      else {{ DepartRL(p)}}
    }} else {{ tau  -> DepartR(p)}};

//Departure RL from root node
DepartRL(p) = tau {{ counts[p] = count;}} -> // LL(I)
             if (vv[p] != v[0]) {{  Skip}}
             else
             {{ ifa (counts[p] != count) {{ tau  -> DepartRL(p)}}
              else {{ tau {{I = 0; count = count + 1;}} -> Skip}}
             }};

//------------------------------end - this part is for root node------------------------------



//------------------------------start - hierarchical SNZI node------------------------------
//Arrival of hierarchical SNZI node
Arrive(p, n) = tau {{s[n * P + p] = 0;}} -> tau {{u[n * P + p] = 0;}} -> ArriveL1(p, n); ArriveL2(p, n); //Skip;

ArriveL1(p, n) =
    if (s[n * P + p] == 0)
    {{  tau {{cc[n * P + p] = c[n]; vv[n * P + p] = v[n];}} -> 
       if (cc[n * P + p] > 1)  //if x.c >= 1 then
       {{ 
         ifa (cc[n * P + p] == c[n] && vv[n * P + p] == v[n])
         {{ tau {{c[n] = cc[n * P + p] + 2; v[n] = vv[n * P + p];}} -> 
           tau {{s[n * P + p] = 1;}} -> Case2(p, n)
         }} else {{ tau  -> Case2(p, n)}}
       }} else {{ Case2(p, n)}}
    }};

Case2(p, n) = if (cc[n * P + p] == 0) // if x.c = 0 then
    {{ 
        ifa (cc[n * P + p] == c[n] && vv[n * P + p] == v[n])
        {{ tau {{c[n] = 1; v[n] = vv[n * P + p] + 1;}} -> tau {{s[n * P + p] = 1;}} ->
           tau {{cc[n * P + p] = 1; vv[n * P + p] = vv[n * P + p] + 1;}} -> Case3(p, n)
        }} else {{ tau  -> Case3(p, n)}}
    }} else {{ Case3(p, n)}};

//if x.c = 1/2 then
Case3(p, n) = if (cc[n * P + p] == 1)
    {{  AG(p, (n - 1)/2);
       ifa (cc[n * P + p] == c[n] && vv[n * P + p] == v[n])
       {{ tau {{c[n] = 2; v[n] = vv[n * P + p];}} -> ArriveL1(p, n)
       }} else {{ tau  -> tau {{u[n * P + p] = u[n * P + p] + 1;}} -> ArriveL1(p, n)}}
    }} else {{ ArriveL1(p, n)}};

ArriveL2(p, n) = if (u[n * P + p] > 0) {{ DG(p, (n - 1)/2); tau {{u[n * P + p] = u[n * P + p] - 1;}} -> ArriveL2(p, n)}}
                 else {{ Skip}};

 //Departure of hierarchical SNZI node
Depart(p, n) =
    tau {{cc[n * P + p] = c[n]; vv[n * P + p] = v[n];}} -> 
    ifa (cc[n * P + p] == c[n] && vv[n * P + p] == v[n])
    {{ tau {{c[n] = cc[n * P + p] - 2; v[n] = vv[n * P + p];}} -> 
      if (cc[n * P + p] == 2)
      {{ DG(p, (n - 1)/2)}}
      //else {{ Skip}}
    }} else {{ tau  -> Depart(p, n)}};

//------------------------------end - hierarchical SNZI node------------------------------

Pro(i, j) = [j < {num_operations}]([] x:{{0..N - 1}}@(AI(i, x); DI(i, x)); Pro(i, j+1));

Q() = q.I -> Q();

SNZI() = (|||x:{{0..P - 1}}@Pro(x, 0)) ||| Q();


//------------------------------Abstract Specification Model------------------------------

//shared variable
var sur = 0;
var ind = 0;

AA(i) = ai.i -> tau{{sur = sur + 1; ind = 1;}} -> ar.i -> Skip;

DA(i) = di.i -> tau{{sur = sur - 1; if (sur == 0) {{ind = 0;}}}} -> dr.i -> Skip;

PA(i, j) = [j < {num_operations}](AA(i); DA(i); PA(i, j+1));

QA() = q.ind -> QA();

SNZIAbs() = (|||x:{{0..P-1}}@PA(x, 0)) ||| QA();

#assert SNZI() refines SNZIAbs();
#assert SNZIAbs() refines SNZI();
"""

    elif algo_id == "kvalued":
        try:
            num_register_values, num_readers = re.split(r'[,\s]+', var_value.strip())
            num_register_values = int(num_register_values)
            num_readers = int(num_readers)
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_register_values < 3) or (num_readers < 1):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        b_elems = [ "0" for _ in range(num_register_values - 1) ]
        b_elems.append("1")
        b_array = "[" + ",".join(b_elems) + "]"
        
        # Generate the Writers process: a sequence of Writer(i) separated by "[]"
        # (e.g., for 3 register values: Writer(0)[]Writer(1)[]Writer(2))
        writers_process = "[]".join(f"Writer({i})" for i in range(num_register_values))
        
        # The Register process composition uses num_readers (within |||{num_readers}@Readers())
        register_process = f"((|||{{{num_readers}}}@Readers()) ||| Writers())"
        
        # Compute the final register value index (last index in B)
        last_index = num_register_values - 1
        
        # Generate the chain of all read_res outputs from 0 to last_index.
        read_res_chain = " ||".join(f"read_res.{i}" for i in range(num_register_values))
        
        processed_code = f"""//shared binary array of size N
var B = {b_array};

////////////////The Concrete Implementation Model//////////////////
Readers() = read_inv -> UpScan(0);
UpScan(i) =  if(B[i] == 1) {{ DownScan(i - 1, i) }} else {{ UpScan(i + 1) }};
DownScan(i, v) =
		ifa(i >= 0) {{
			if(B[i] == 1) {{ DownScan(i - 1, i) }} else {{ DownScan(i - 1, v) }}
		}} else {{
			t -> read_res.v -> Readers()
		}};

Writer(i) = write_inv.i -> t{{B[i] = 1;}} -> WriterDownScan(i-1);
WriterDownScan(i) = if(i >= 0 ) {{ t{{B[i] = 0;}} -> WriterDownScan(i-1) }} else {{ write_res -> Skip }} ;

Writers() = ({writers_process}); Writers();
Register() = {register_process};

////////////////The Properties//////////////////
#assert Register() deadlockfree;
#assert Register() |= []<> read_res.{last_index};
#assert Register() |= [](read_inv -> <>({read_res_chain}));
"""

    elif algo_id == "java":
        try:
            num_waiting, system_type = re.split(r'[,\s]+', var_value.strip())
            num_waiting = int(num_waiting)
            system_type = system_type.lower()
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_waiting < 1) or (system_type not in ['finite_threads', 'infinite_threads']):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        if system_type == "infinite_threads":
            processed_code = f'''#define N {num_waiting}; /* max num of threads that can wait at waiting state */

/* msg */
#define put_fast 100;
#define get_fast 101;
#define go 102;
#define request 103;
#define release 104;
#define get_slow 105;
#define put_slow 106;

channel ascChan 0;
var count =0;
var access = false;

handoff() = ascChan?release -> ascChan?request -> ascChan!go -> handoff()
	     [] ascChan?request -> ascChan?release -> ascChan!go -> handoff();

shared_obj() = ascChan?get_fast -> Busy_0();

Busy_0() = ascChan?put_fast -> shared_obj()
    	[] ascChan?get_slow -> inc{{count = count+1;}} -> Busy_N();

Busy_N() = [count < N]ascChan?get_slow -> inc{{count = count+1;}} -> Busy_N()
	    [] ascChan?put_slow -> dec{{count = count -1;}} ->
        	(
		      if(count == 0){{
			     Busy_0()
		      }} else {{
			     Busy_N()
		      }}
	       );
	       	       

my_thread() = ascChan!get_fast -> enterCritical{{access = true;}} ->Owner()
	       [] ascChan!get_slow -> ascChan!request -> ascChan?go -> enterCritical{{access = true;}} ->Owner();

Owner() = leaveCritical{{access = false;}} ->
          (
		       ascChan!put_fast -> my_thread()
	    	[] ascChan!put_slow -> ascChan!release -> my_thread()
	      );

System() = ((|||{{..}}@my_thread())||| handoff() ||| shared_obj());

#assert System() deadlockfree;
#define someoneaccess access == true;
#assert System() |= []<>someoneaccess;
'''
        else: # finite_threads
            processed_code = f'''#define N {num_waiting}; /* max num of threads that can wait at waiting state */

/* msg */
#define put_fast 100;
#define get_fast 101;
#define go 102;
#define request 103;
#define release 104;
#define get_slow 105;
#define put_slow 106;

channel ascChan 0;
var count =0;
var access = false;

handoff() = ascChan?release -> ascChan?request -> ascChan!go -> handoff()
	     [] ascChan?request -> ascChan?release -> ascChan!go -> handoff();

shared_obj() = ascChan?get_fast -> Busy_0();

Busy_0() = ascChan?put_fast -> shared_obj()
    	[] ascChan?get_slow -> inc{{count = count+1;}} -> Busy_N();

Busy_N() = ascChan?get_slow -> inc{{count = count+1;}} -> Busy_N()
	    [] ascChan?put_slow -> dec{{count = count -1;}} ->
        	(
		      if(count == 0){{
			     Busy_0()
		      }} else {{
			     Busy_N()
		      }}
	       );
	       	       

my_thread() = ascChan!get_fast -> enterCritical{{access = true;}} ->Owner()
	       [] ascChan!get_slow -> ascChan!request -> ascChan?go -> enterCritical{{access = true;}} ->Owner();

Owner() = leaveCritical{{access = false;}} ->
          (
		       ascChan!put_fast -> my_thread()
	    	[] ascChan!put_slow -> ascChan!release -> my_thread()
	      );

System() = ((|||{{N}}@my_thread())||| handoff() ||| shared_obj());

#assert System() deadlockfree;
#define someoneaccess access == true;
#assert System() |= []<>someoneaccess;
'''

    elif algo_id == "1dchannel":
        if var_value < 2:
            raise ValueError("Please enter a valid number which is at least 2!")
        
        processed_code = f'''#define N {var_value};

//a synchronous channel array
channel right[N+1] 0;  

//example of channel array to send data in one action
Send() = right[0]!5 -> Send();
//example of channel array to receive data in one action
Receive() = right[N]?x -> Receive();

COPY(i) = right[i]?x -> right[i+1]!x -> COPY(i);
PIPE() = ||| i:{{0..(N-1)}} @ COPY(i);

System() = PIPE() ||| Send() ||| Receive();

#assert System() deadlockfree;'''

    elif algo_id == "2dchannel":
        try:
            num_rows, num_cols = re.split(r'[,\s]+', var_value.strip())
            num_rows = int(num_rows)
            num_cols = int(num_cols)
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_rows < 2) or (num_cols < 2):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        processed_code = f'''#define M {num_rows}; // row number 
#define N {num_cols}; // column number

// The following are one-dimension synchrnous channle arrays used to simulate the 2-d synchronous channel array
// channel right[i][j] is represented as c[i*N + j] 
channel right[M*N] 0;
channel down[M*N] 0;

//The system is a network of cells, messages transimit from one cell to its adjacent cell horizontally or vertically
Send(i,j) = right[i*N]!i*N -> Send(i,j)
         [] down[j]!j -> Send(i,j);
 
Receive(i,j) = right[(i+1)*N-1]?x -> Receive(i,j)
         [] down[(M-1)*N+j]?x -> Receive(i,j);
         
Cell(i,j) = [(j+1)%N != 0]right[i*N+j]?x -> right[(i*N+j+1)]!x -> Cell(i,j)
         [] [(i+1)%M != 0]down[i*N+j]?x -> down[((i+1)*N+j)]!x -> Cell(i,j);
         
System() = ||| i:{{0..(M-1)}}@(|||j:{{0..(N-1)}}@(Send(i,j)|||Receive(i,j)|||Cell(i,j)));

#assert System() deadlockfree;
'''

    elif algo_id == "dbm":
        try:
            num_timers, clock_ceiling = re.split(r'[,\s]+', var_value.strip())
            num_timers = int(num_timers)
            clock_ceiling = int(clock_ceiling)
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_timers < 1) or (clock_ceiling < 1):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        bound = num_timers * clock_ceiling
        processed_code = f'''#import "PAT.Lib.DBM";
#import "PAT.Lib.Set";
#import "PAT.Math";

//DBM model has two DBMs: dbm1 and dbm2
#define N {num_timers};//the number of clocks of each DBM
#define Ceiling {clock_ceiling};//the number of constraints added in each DBM
#define Bound {bound}; //the timer bound

var<DBM> dbm1 = new DBM(Ceiling);
var<Set> timers1 = new Set();
var timerCount1 = 0;
var timerID1 = 1;
var result1 = false;
var isBounded = true;
var containsClock1 = false;
var stopped = false;


DBMTest1() = ifa(timerCount1 < N) 
			 {{
				newTimerID{{timerID1 = dbm1.GetNewTimerID();stopped=false}} -> AddTimer.timerID1{{dbm1.AddTimer(timerID1); timers1.Add(timerID1); timerCount1 = timers1.Count();}} -> 
				(Delay{{dbm1.Delay()}} -> 			
				(OneCycle1; 
					 check{{result1 = dbm1.IsConstraintNotSatisfied(); isBounded=dbm1.IsTimersBounded(Bound);}} ->
					 ifa (!result1)
					 {{
					 	ConstraintSatisfied -> (KeepTProcess1(timerCount1, call(Pow, 2, timerCount1)); (DBMTest1() [] ResetProcess1(timerCount1)))
					 }}
					 else 
					 {{
					 	ConstraintNotSatisfied{{dbm1 = new DBM(Ceiling); timers1 = new Set(); timerCount1 =0; timerID1 = 1;}} -> DBMTest1()
					 }}
					)
				)
			 }}
			 else
			 {{
				stop{{stopped =true;}} -> DBMTest1()
			 }};

OneCycle1() = (AddCProcess1(timerCount1); OneCycle1)
		      [] (Clone{{dbm1.Clone()}} -> OneCycle1)
	    	  [] Skip;
			
ResetProcess1(size) = ifa(size > 0) {{ 
					 	[]t:{{0..size-1}}@ResetTimer{{dbm1.ResetTimer(timers1.Get(t))}} -> DBMTest1()
					  }} else {{
					 	 DBMTest1()
					  }};
			
KeepTProcess1(size, powset) =  ifa(size > 0) 
					 		   {{
						 			ifa(powset ==1)
						 			{{
						 				KeepTimers.1{{dbm1 = dbm1.KeepTimers(timers1.GetSubsetByIndex(1)); timerCount1 = timers1.Count(); containsClock1=timers1.Contains(1); }} -> Skip
						 			}}
						 	        else
						 			{{
					 					[] t:{{1..powset-1}}@KeepTimers.t{{dbm1 = dbm1.KeepTimers(timers1.GetSubsetByIndex(t)); timerCount1 = timers1.Count(); containsClock1=timers1.Contains(1);}} -> Skip
						 			}}
					 		   }};					

AddCProcess1(size) = ifa(size > 0) {{
						([] t:{{0..size-1}}@ ([]op:{{0..2}}@ ([]value:{{0..Ceiling}}@ AddConstraint.t.op.value{{dbm1.AddConstraint(timers1.Get(t), op, value);}} -> Skip )))
					 }};	 
					
					
#assert DBMTest1 deadlockfree;

#define goal timerID1 == 0;
#assert DBMTest1 reaches goal;

#define goal1 isBounded == true;
#assert DBMTest1 |= []goal1;

#define goal2 stopped==true || containsClock1 == false;
#assert DBMTest1 |= []<>goal2;	
	
//==============================================================================
var<DBM> dbm2 = new DBM(Ceiling);
var<Set> timers2 = new Set();
var timerCount2 = 0;
var timerID2 = 1;
var result2 = false;
var isBounded2 = true;
var containsClock2 = false;
var stopped2 = false;

DBMTest2() = ifa(timerCount2 < N)
			{{
				newTimerID{{timerID2 = dbm2.GetNewTimerID();stopped2=false}} -> AddTimer.timerID2{{dbm2.AddTimer(timerID2); timers2.Add(timerID2); timerCount2 = timers2.Count();}} -> 
				(Delay{{dbm2.Delay()}} -> 			
				(OneCycle2; 
					 check{{result2 = dbm2.IsConstraintNotSatisfied(); isBounded2=dbm2.IsTimersBounded(Bound);}} ->
					 ifa (!result2)
					 {{
					 	ConstraintSatisfied -> (KeepTProcess2(timerCount2, call(Pow, 2, timerCount2)); (DBMTest2() [] ResetProcess2(timerCount2)))
					 }}
					 else 
					 {{
					 	ConstraintNotSatisfied{{dbm2 = new DBM(Ceiling); timers2 = new Set(); timerCount2 =0; timerID2 = 1;}} -> DBMTest2()
					 }}
					)
				)
			}}
			else
			{{
				stop{{stopped2 =true;}} -> DBMTest2()
			}}
			;

OneCycle2 = (AddCProcess2(timerCount2); OneCycle2)
		[] (Clone{{dbm2.Clone()}} -> OneCycle2)
		[] Skip;
			
ResetProcess2(size) = ifa(size > 0) {{ 
					 	[]t:{{0..size-1}}@ResetTimer{{dbm2.ResetTimer(timers2.Get(t))}} -> DBMTest2()
					 }} else {{
					 	DBMTest2()
					 }};
			
KeepTProcess2(size, powset) = ifa(size > 0) 
					 		  {{
						 			ifa(powset ==1)
						 			{{
						 				KeepTimers.1{{dbm2 = dbm2.KeepTimers(timers2.GetSubsetByIndex(1)); timerCount2 = timers2.Count(); containsClock2=timers2.Contains(1); }} -> Skip
						 			}}
						 	        else
						 			{{
					 					[] t:{{1..powset-1}}@KeepTimers.t{{dbm2 = dbm2.KeepTimers(timers2.GetSubsetByIndex(t)); timerCount2 = timers2.Count(); containsClock2=timers2.Contains(1);}} -> Skip
						 			}}
					 		  }};					

AddCProcess2(size) = ifa(size > 0) {{
						([] t:{{0..size-1}}@ ([]op:{{0..2}}@ ([]value:{{0..Ceiling}}@ AddConstraint.t.op.value{{dbm2.AddConstraint(timers2.Get(t), op, value);}} -> Skip )))
					 }};	 

//==============================================================================
aDBMTest = DBMTest1 ||| DBMTest2;

#assert aDBMTest deadlockfree;

#define goal3 timerID1 == 0;
#assert aDBMTest reaches goal3;

#define goal4 isBounded == true && isBounded2 == true;
#assert aDBMTest |= []goal4;

#define goal5 (stopped==true || containsClock1 == false) && (stopped2 ==true || containsClock2 == false);
#assert aDBMTest |= []<>goal5;
'''
    elif algo_id == "peg":
        if var_value < 1 or var_value > 9:
            raise ValueError("Please enter a valid number which is at least 2!")
        
        if var_value == 1:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 1 =========
#define initEmptyX 3;
#define initEmptyY 3;
#define W 7;
#define H 7;
var board[H][W] = 
		  [X,X,P,P,P,X,X,
           X,X,P,P,P,X,X,
           S,S,P,P,P,P,P,
           P,P,P,E,P,P,P,
           S,S,P,P,P,P,P,
           X,X,S,P,S,X,X,
           X,X,S,P,S,X,X];
    
var pegsCounter = 32;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        elif var_value == 2:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 2 =========
#define initEmptyX 2;
#define initEmptyY 3;
#define W 7;
#define H 6;
var board[H][W] = 
		  [X,X,P,P,P,X,X,
           S,S,P,P,P,P,P,
           P,P,P,E,P,P,P,
           S,S,P,P,P,P,P,
           X,X,S,P,S,X,X,
           X,X,S,P,S,X,X];
    
var pegsCounter = 29;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        elif var_value == 3:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 3 =========
#define initEmptyX 2;
#define initEmptyY 3;
#define W 6;
#define H 6;
var board[H][W] = 
	         [X,X,P,P,P,X,
           S,S,P,P,P,P,
           P,P,P,E,P,P,
           S,S,P,P,P,P,
           X,X,S,P,S,X,
           X,X,S,P,S,X];
    
var pegsCounter = 26;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        elif var_value == 4:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 4 =========
#define initEmptyX 2;
#define initEmptyY 2;
#define W 5;
#define H 6;
var board[H][W] = 
	         [X,P,P,P,X,
           S,P,P,P,P,
           P,P,E,P,P,
           S,P,P,P,P,
           X,S,P,S,X,
           X,S,P,S,X];
    
var pegsCounter = 23;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        elif var_value == 5:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 5 =========
#define initEmptyX 1;
#define initEmptyY 2;
#define W 5;
#define H 5;
var board[H][W] = 
	         [S,P,P,P,P,
           P,P,E,P,P,
           S,P,P,P,P,
           X,S,P,S,X,
           X,S,P,S,X];
    
var pegsCounter = 20;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        elif var_value == 6:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 6 =========
#define initEmptyX 4;
#define initEmptyY 3;
#define W 7;
#define H 8;
var board[H][W] = 
	         [X,X,P,P,P,X,X,
           X,X,P,P,P,X,X,
           X,X,P,P,P,X,X,
           S,S,P,P,P,P,P,
           P,P,P,E,P,P,P,
           S,S,P,P,P,P,P,
           X,X,S,P,S,X,X,
           X,X,S,P,S,X,X];
    
var pegsCounter = 48;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        elif var_value == 7:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 7 =========
#define initEmptyX 4;
#define initEmptyY 3;
#define W 7;
#define H 8;
var board[H][W] = 
	         [X,X,P,P,P,P,X,
           X,X,P,P,P,P,X,
           X,X,P,P,P,P,X,
           S,S,P,P,P,P,P,
           S,S,P,E,P,P,P,
           S,S,P,P,P,P,P,
           X,X,S,S,S,X,X,
           X,X,S,S,S,X,X];
    
var pegsCounter = 38;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        elif var_value == 8:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 8 =========
#define initEmptyX 4;
#define initEmptyY 3;
#define W 7;
#define H 8;
var board[H][W] = 
	         [X,P,P,P,P,P,X,
           X,P,P,P,P,P,X,
           X,P,P,P,P,P,X,
           S,S,P,P,P,P,P,
           S,S,P,E,P,P,P,
           S,S,P,P,P,S,S,
           X,X,S,S,S,X,X,
           X,X,S,S,S,X,X];
    
var pegsCounter = 41;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''
        else:
            processed_code = f'''#define X -1;
#define P 1;
#define E 2;
#define S 1; //sticky has the same value as P now.

//===== Board 9 =========
#define initEmptyX 4;
#define initEmptyY 3;
#define W 7;
#define H 8;
var board[H][W] = 
	         [P,P,P,P,P,P,P,
           P,P,P,P,P,P,P,
           P,P,P,P,P,P,P,
           S,S,P,P,P,P,P,
           S,S,P,E,P,P,S,
           S,S,S,P,S,S,S,
           X,X,S,S,S,X,X,
           X,X,S,S,S,X,X];
    
var pegsCounter = 47;

//four different ways of jumping
Up(i, j) = [i-2>=0]([board[i-2][j]==E && board[i-1][j]== P]up{{board[i-2][j] = P; board[i-1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Left(i, j) = [j-2>=0]([board[i][j-2]==E && board[i][j-1]== P]left{{board[i][j-2] = P; board[i][j-1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 
Down(i, j) = [i+2<H]([board[i+2][j] != X && board[i+2][j]==E && board[i+1][j]== P]down{{board[i+2][j] = P; board[i+1][j] = E; board[i][j] = E; pegsCounter--;}} -> Game());  
Right(i, j) = [j+2<W]([board[i][j+2] != X && board[i][j+2]==E && board[i][j+1]== P]right{{board[i][j+2] = P; board[i][j+1] = E; board[i][j] = E; pegsCounter--;}} -> Game()); 

//if there is a peg in the cell, it makes four diffferent moves
Peg(i,j) = [board[i][j]==P](Up(i,j) [] Left(i,j) [] Down(i,j) [] Right(i,j));
Game() = []i:{{0..H-1}};j:{{0..W-1}}@ Peg(i,j);

#define goal pegsCounter == 1 && board[initEmptyX][initEmptyY] == P;
#assert Game() reaches goal;
'''

    elif algo_id == "huarongdao":
        if var_value.lower() == "general":
            processed_code = f'''//The version of this Hua Rong Dao game is Bi Yi Heng Kong

//The game goal is find a solution which is not required to have minimum number of steps .

//This game huarongdao contains  4 bing (b1..b4) , 5 jiang (j5..j9) and 1 caocao (cc),2 space(sp)
//noted that enumerate data values are from 0 such that sp=0,b1=1 etc.That feature is used in this mode.
//j5:guanyu,j6:zhangfei,j7:zhaoyun,j8:machao,j9:huangzhongb1:bing,b2:ding,b3:zu,b4:yong
enum {{sp,b1,b2,b3,b4,j5,j6,j7,j8,j9,cc}};

//this array indicates jiang[i] is set either horizontally or vertically
//1--vertical  0--horizontal 99-not used
hvar jiang[11] = [99,99,99,99,99,1,1,1,1,1,99];

//The board can be modified to check other stages and it is the only structure needed to change
//one jiang occupys 2 position such that there are two j5.others are similar
//99 is just a number which indicates the boundary. It can be changed to any number lager than 10
hvar board[42] = [ 99,99,99,99,99,99,
                   99,j7,j7,cc,cc,99,
                   99,j8,j8,cc,cc,99,
                   99,j6,j6,j5,j5,99,
                   99,b1,b4,b2,j9,99,
                   99,b3,sp,sp,j9,99,
                   99,99,99,99,99,99 ];          
                   

//all moves are described in it
var seq[42] = [99(42)];

//the two space position. Setting to 6 only for skip the Simluation(F6) checking 
hvar space1 = 6;
hvar space2 = 6;

//max steps which we allow PAT to try 
#define MAX_STEP 90;

//standard game steps counter
hvar counter=0;
hvar last_move=0;

#define UP 1;
#define DOWN 2;
#define LEFT 3;
#define RIGHT 4;

hvar last_direction = 0;

//initialize the game
Initial() = INIT{{
                    counter=0;
                    last_move=0;
	                seq = board;
	                //set 7 to skip the boundary
	                var i = 7;
	                //initialize all jiang's placing directions(vertical or horizontal) and space positions
	                while(i<36)
	                {{
	                	if(seq[i]-seq[i-1]==0 && seq[i]!=cc && seq[i]!=sp && seq[i]!=99) jiang[seq[i]]=0;
	                	if(seq[i]==sp)
	                	{{
	                	    if(space1==6) space1 = i;
	                	    else space2 = i;
	                	}}
	                    i++;                              	
	                }}
                }}->Skip;
                

//Bing's move
Bing(i) = [((seq[space1+6]==i) || (seq[space2+6]==i)) && !(last_move==i && last_direction==DOWN) && counter<=MAX_STEP]
          bingup.i{{
                     if(seq[space1+6]==i)
                     {{seq[space1]=i;space1=space1+6;seq[space1]=sp}}
                     else
                     {{seq[space2]=i;space2=space2+6;seq[space2]=sp}}
                     if (last_move!=i) counter++;
                     last_move=i;
                     last_direction=UP;
                   }}->Bing(i)
          []
          [((seq[space1-6]==i) || (seq[space2-6]==i)) && !(last_move==i && last_direction==UP) && counter<=MAX_STEP]
          bingdown.i{{
	                    if(seq[space1-6]==i)
	                    {{seq[space1]=i;space1=space1-6;seq[space1]=sp}}
	                    else
	                    {{seq[space2]=i;space2=space2-6;seq[space2]=sp}}
	                    if (last_move!=i) counter++;
                        last_move=i;
                        last_direction=DOWN;
	                }}->Bing(i)
	      []
	      [((seq[space1+1]==i) || (seq[space2+1]==i)) && !(last_move==i && last_direction==RIGHT) && counter<=MAX_STEP]
	      bingleft.i{{
	                    if(seq[space1+1]==i)
	                    {{seq[space1]=i;space1=space1+1;seq[space1]=sp}}
	                    else
	                    {{seq[space2]=i;space2=space2+1;seq[space2]=sp}}
	                    if (last_move!=i) counter++;
                        last_move=i;
                        last_direction=LEFT;
	                }}->Bing(i)
	      []
	      [((seq[space1-1]==i) || (seq[space2-1]==i)) && !(last_move==i && last_direction==LEFT) && counter<=MAX_STEP]
	      bingright.i{{
	                     if(seq[space1-1]==i)
	                     {{seq[space1]=i;space1=space1-1;seq[space1]=sp}}
	                     else
	                     {{seq[space2]=i;space2=space2-1;seq[space2]=sp}}
	                     if (last_move!=i) counter++;
                         last_move=i;
                         last_direction=RIGHT;
	                 }}->Bing(i);

//Jiang's move
Jiang(i) = ifa(jiang[i]==0)
           {{
           		[seq[space1+6]==i && seq[space2+6]==i  && !(last_move==i && last_direction==DOWN) && counter<=MAX_STEP]
           		jiangup.i{{
           		             seq[space1]=i;
           		             seq[space2]=i;
           		             space1=space1+6;
           		             space2=space2+6;
           		             seq[space1]=sp;
           		             seq[space2]=sp;
           		             if (last_move!=i) counter++;
                             last_move=i;
                             last_direction=UP;
           		         }}->Jiang(i)
           		[]
           		[seq[space1-6]==i && seq[space2-6]==i && !(last_move==i && last_direction==UP) && counter<=MAX_STEP]
           		jiangdown.i{{
           		               seq[space1]=i;
           		               seq[space2]=i;
           		               space1=space1-6;
           		               space2=space2-6;
           		               seq[space1]=sp;
           		               seq[space2]=sp;
           		               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=DOWN;
           		           }}->Jiang(i)	
           		[]
           		[((seq[space1+1]==i) || (seq[space2+1]==i)) && !(last_move==i && last_direction==RIGHT) && counter<=MAX_STEP]
           		jiangleft.i{{
           		               if(seq[space1+1]==i)
           		               {{seq[space1]=i;space1=space1+2;seq[space1]=sp}}
           		               else
           		               {{seq[space2]=i;space2=space2+2;seq[space2]=sp}}
           		               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=LEFT;
           		           }}->Jiang(i)	
           		[]           
           		[((seq[space1-1]==i) || (seq[space2-1]==i)) && !(last_move==i && last_direction==LEFT) && counter<=MAX_STEP]
           		jiangright.i{{
           		                if(seq[space1-1]==i)
           		                {{seq[space1]=i;space1=space1-2;seq[space1]=sp}}
           		                else
           		                {{seq[space2]=i;space2=space2-2;seq[space2]=sp}}
           		                if (last_move!=i) counter++;
                                last_move=i;
                                last_direction=RIGHT;
           		            }}->Jiang(i)
           }}
           else ifa(jiang[i]==1)
           {{
                [((seq[space1+6]==i) || (seq[space2+6]==i)) && !(last_move==i && last_direction==DOWN) && counter<=MAX_STEP]
                jiangup.i{{
                             if(seq[space1+6]==i)
                             {{seq[space1]=i;space1=space1+12;seq[space1]=sp}}
                             else
                             {{seq[space2]=i;space2=space2+12;seq[space2]=sp}}
                             if (last_move!=i) counter++;
                             last_move=i;
                             last_direction=UP;
                         }}->Jiang(i)
                []
                [((seq[space1-6]==i) || (seq[space2-6]==i)) && !(last_move==i && last_direction==UP)&& counter<=MAX_STEP]
                jiangdown.i{{
                               if(seq[space1-6]==i)
                               {{seq[space1]=i;space1=space1-12;seq[space1]=sp}}
                               else
                               {{seq[space2]=i;space2=space2-12;seq[space2]=sp}}
                               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=DOWN;
                           }}->Jiang(i)
                []
                [seq[space1+1]==i && seq[space2+1]==i && !(last_move==i && last_direction==RIGHT) && counter<=MAX_STEP]
                jiangleft.i{{
                               seq[space1]=i;
           		               seq[space2]=i;
           		               space1=space1+1;
           		               space2=space2+1;
           		               seq[space1]=sp;
           		               seq[space2]=sp;
           		               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=LEFT;
           		           }}->Jiang(i)	
           		[]
           		[seq[space1-1]==i && seq[space2-1]==i && !(last_move==i && last_direction==LEFT) && counter<=MAX_STEP]
                jiangright.i{{
                                seq[space1]=i;
           		                seq[space2]=i;
           		                space1=space1-1;
           		                space2=space2-1;
           		                seq[space1]=sp;
           		                seq[space2]=sp;
           		                if (last_move!=i) counter++;
                                last_move=i;
                                last_direction=RIGHT;
           		            }}->Jiang(i)	
           }};

//Caocao's move           
CaocaoMove() = [seq[space1+6]==cc && seq[space2+6]==cc && !(last_move==cc && last_direction==DOWN) && counter<=MAX_STEP]
           caocaoup{{
                       seq[space1]=cc;
                       seq[space2]=cc;
                       space1=space1+12;
                       space2=space2+12;
                       seq[space1]=sp;
           		       seq[space2]=sp;
           		       if (last_move!=cc) counter++;
                       last_move=cc;
                       last_direction=UP; 
                   }}->CaocaoMove()
           []
           [seq[space1-6]==cc && seq[space2-6]==cc && !(last_move==cc && last_direction==UP) && counter<=MAX_STEP]
           caocaodown{{
                         seq[space1]=cc;
                         seq[space2]=cc;
                         space1=space1-12;
                         space2=space2-12;
                         seq[space1]=sp;
           		         seq[space2]=sp;
           		         if (last_move!=cc) counter++;
                         last_move=cc;
                         last_direction=DOWN;
                     }}->CaocaoMove()
           []
           [seq[space1+1]==cc && seq[space2+1]==cc && !(last_move==cc && last_direction==RIGHT) && counter<=MAX_STEP]
           caocaoleft{{
                         seq[space1]=cc;
                         seq[space2]=cc;
                         space1=space1+2;
                         space2=space2+2;
                         seq[space1]=sp;
           		         seq[space2]=sp;
           		         if (last_move!=cc) counter++;
                         last_move=cc;
                         last_direction=LEFT;
                     }}->CaocaoMove()
           []
           [seq[space1-1]==cc && seq[space2-1]==cc && !(last_move==cc && last_direction==LEFT) && counter<=MAX_STEP]
           caocaoright{{
                          seq[space1]=cc;
                          seq[space2]=cc;
                          space1=space1-2;
                          space2=space2-2;
                          seq[space1]=sp;
           		          seq[space2]=sp;
           		          if (last_move!=cc) counter++;
                          last_move=cc;
                          last_direction=RIGHT;
                      }}->CaocaoMove();

//10 entities synchronize                                        
BingMove() = ||x:{{b1..b4}}@Bing(x);
JiangMove() = ||x:{{j5..j9}}@Jiang(x);
Game() = Initial();(BingMove()||JiangMove()||CaocaoMove());


//caocao arrives the exit
#define goal (seq[26]==cc && seq[27]==cc && seq[32]==cc && seq[33]==cc);

//try to find out the best solution
#assert Game() reaches goal with min(counter);
'''
        elif var_value.lower() == "optimal":
            processed_code = f'''//The version of this Hua Rong Dao game is Bi Yi Heng Kong

//The game goal is find a solution which has minimum number of steps .


//This game huarongdao contains  4 bing (b1..b4) , 5 jiang (j5..j9) and 1 caocao (cc),2 space(sp)
//noted that enum data values from 0 such that sp=0,b1=1 etc.That feature is used in this mode.
//j5:guanyu,j6:zhangfei,j7:zhaoyun,j8:machao,j9:huangzhongb1:bing,b2:ding,b3:zu,b4:yong
enum {{sp,b1,b2,b3,b4,j5,j6,j7,j8,j9,cc}};

//this array indicates  jiang[i] is put as either horizontal or vertical
//1--vertical  0--horizontal 99-not used
hvar jiang[11] = [99,99,99,99,99,1,1,1,1,1,99];

//board can be modified to check other stages and it is the only structure needed to change
//one jiang occupys 2 position such that there are two j5.others are similar
//99 is just a number which indicates the boundary. It can be changed to any number lager than 10
hvar board[42] = [ 99,99,99,99,99,99,
                   99,j7,j7,cc,cc,99,
                   99,j8,j8,cc,cc,99,
                   99,j6,j6,j5,j5,99,
                   99,b1,b4,b2,j9,99,
                   99,b3,sp,sp,j9,99,
                   99,99,99,99,99,99 ];          
                   

//all moves happen in it
var seq[42] = [99(42)];

//the two space position. Setting to 6 only for skip the Simluation(F6) checking 
hvar space1 = 6;
hvar space2 = 6;

//max steps which we allow the PAT to try 
#define MAX_STEP 41;

//standard game steps counter
var counter=0;
hvar last_move=0;

#define UP 1;
#define DOWN 2;
#define LEFT 3;
#define RIGHT 4;

hvar last_direction = 0;

//initialize the game
Initial() = INIT{{
                    counter=0;
                    last_move=0;
	                seq = board;
	                //set 7 to skip the boundary
	                var i = 7;
	                //initialize all jiang's placing direction(vertical or horizontal) and space position
	                while(i<36)
	                {{
	                	if(seq[i]-seq[i-1]==0 && seq[i]!=cc && seq[i]!=sp && seq[i]!=99) jiang[seq[i]]=0;
	                	if(seq[i]==sp)
	                	{{
	                	    if(space1==6) space1 = i;
	                	    else space2 = i;
	                	}}
	                    i++;                              	
	                }}
                }}->Skip;
                

//Bing's move
Bing(i) = [((seq[space1+6]==i) || (seq[space2+6]==i)) && !(last_move==i && last_direction==DOWN) && counter<=MAX_STEP]
          bingup.i{{
                     if(seq[space1+6]==i)
                     {{seq[space1]=i;space1=space1+6;seq[space1]=sp}}
                     else
                     {{seq[space2]=i;space2=space2+6;seq[space2]=sp}}
                     if (last_move!=i) counter++;
                     last_move=i;
                     last_direction=UP;
                   }}->Bing(i)
          []
          [((seq[space1-6]==i) || (seq[space2-6]==i)) && !(last_move==i && last_direction==UP) && counter<=MAX_STEP]
          bingdown.i{{
	                    if(seq[space1-6]==i)
	                    {{seq[space1]=i;space1=space1-6;seq[space1]=sp}}
	                    else
	                    {{seq[space2]=i;space2=space2-6;seq[space2]=sp}}
	                    if (last_move!=i) counter++;
                        last_move=i;
                        last_direction=DOWN;
	                }}->Bing(i)
	      []
	      [((seq[space1+1]==i) || (seq[space2+1]==i)) && !(last_move==i && last_direction==RIGHT) && counter<=MAX_STEP]
	      bingleft.i{{
	                    if(seq[space1+1]==i)
	                    {{seq[space1]=i;space1=space1+1;seq[space1]=sp}}
	                    else
	                    {{seq[space2]=i;space2=space2+1;seq[space2]=sp}}
	                    if (last_move!=i) counter++;
                        last_move=i;
                        last_direction=LEFT;
	                }}->Bing(i)
	      []
	      [((seq[space1-1]==i) || (seq[space2-1]==i)) && !(last_move==i && last_direction==LEFT) && counter<=MAX_STEP]
	      bingright.i{{
	                     if(seq[space1-1]==i)
	                     {{seq[space1]=i;space1=space1-1;seq[space1]=sp}}
	                     else
	                     {{seq[space2]=i;space2=space2-1;seq[space2]=sp}}
	                     if (last_move!=i) counter++;
                         last_move=i;
                         last_direction=RIGHT;
	                 }}->Bing(i);

//Jiang's move
Jiang(i) = ifa(jiang[i]==0)
           {{
           		[seq[space1+6]==i && seq[space2+6]==i  && !(last_move==i && last_direction==DOWN) && counter<=MAX_STEP]
           		jiangup.i{{
           		             seq[space1]=i;
           		             seq[space2]=i;
           		             space1=space1+6;
           		             space2=space2+6;
           		             seq[space1]=sp;
           		             seq[space2]=sp;
           		             if (last_move!=i) counter++;
                             last_move=i;
                             last_direction=UP;
           		         }}->Jiang(i)
           		[]
           		[seq[space1-6]==i && seq[space2-6]==i && !(last_move==i && last_direction==UP) && counter<=MAX_STEP]
           		jiangdown.i{{
           		               seq[space1]=i;
           		               seq[space2]=i;
           		               space1=space1-6;
           		               space2=space2-6;
           		               seq[space1]=sp;
           		               seq[space2]=sp;
           		               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=DOWN;
           		           }}->Jiang(i)	
           		[]
           		[((seq[space1+1]==i) || (seq[space2+1]==i)) && !(last_move==i && last_direction==RIGHT) && counter<=MAX_STEP]
           		jiangleft.i{{
           		               if(seq[space1+1]==i)
           		               {{seq[space1]=i;space1=space1+2;seq[space1]=sp}}
           		               else
           		               {{seq[space2]=i;space2=space2+2;seq[space2]=sp}}
           		               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=LEFT;
           		           }}->Jiang(i)	
           		[]           
           		[((seq[space1-1]==i) || (seq[space2-1]==i)) && !(last_move==i && last_direction==LEFT) && counter<=MAX_STEP]
           		jiangright.i{{
           		                if(seq[space1-1]==i)
           		                {{seq[space1]=i;space1=space1-2;seq[space1]=sp}}
           		                else
           		                {{seq[space2]=i;space2=space2-2;seq[space2]=sp}}
           		                if (last_move!=i) counter++;
                                last_move=i;
                                last_direction=RIGHT;
           		            }}->Jiang(i)
           }}
           else ifa(jiang[i]==1)
           {{
                [((seq[space1+6]==i) || (seq[space2+6]==i)) && !(last_move==i && last_direction==DOWN) && counter<=MAX_STEP]
                jiangup.i{{
                             if(seq[space1+6]==i)
                             {{seq[space1]=i;space1=space1+12;seq[space1]=sp}}
                             else
                             {{seq[space2]=i;space2=space2+12;seq[space2]=sp}}
                             if (last_move!=i) counter++;
                             last_move=i;
                             last_direction=UP;
                         }}->Jiang(i)
                []
                [((seq[space1-6]==i) || (seq[space2-6]==i)) && !(last_move==i && last_direction==UP)&& counter<=MAX_STEP]
                jiangdown.i{{
                               if(seq[space1-6]==i)
                               {{seq[space1]=i;space1=space1-12;seq[space1]=sp}}
                               else
                               {{seq[space2]=i;space2=space2-12;seq[space2]=sp}}
                               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=DOWN;
                           }}->Jiang(i)
                []
                [seq[space1+1]==i && seq[space2+1]==i && !(last_move==i && last_direction==RIGHT) && counter<=MAX_STEP]
                jiangleft.i{{
                               seq[space1]=i;
           		               seq[space2]=i;
           		               space1=space1+1;
           		               space2=space2+1;
           		               seq[space1]=sp;
           		               seq[space2]=sp;
           		               if (last_move!=i) counter++;
                               last_move=i;
                               last_direction=LEFT;
           		           }}->Jiang(i)	
           		[]
           		[seq[space1-1]==i && seq[space2-1]==i && !(last_move==i && last_direction==LEFT) && counter<=MAX_STEP]
                jiangright.i{{
                                seq[space1]=i;
           		                seq[space2]=i;
           		                space1=space1-1;
           		                space2=space2-1;
           		                seq[space1]=sp;
           		                seq[space2]=sp;
           		                if (last_move!=i) counter++;
                                last_move=i;
                                last_direction=RIGHT;
           		            }}->Jiang(i)	
           }};

//Caocao's move           
CaocaoMove() = [seq[space1+6]==cc && seq[space2+6]==cc && !(last_move==cc && last_direction==DOWN) && counter<=MAX_STEP]
           caocaoup{{
                       seq[space1]=cc;
                       seq[space2]=cc;
                       space1=space1+12;
                       space2=space2+12;
                       seq[space1]=sp;
           		       seq[space2]=sp;
           		       if (last_move!=cc) counter++;
                       last_move=cc;
                       last_direction=UP; 
                   }}->CaocaoMove()
           []
           [seq[space1-6]==cc && seq[space2-6]==cc && !(last_move==cc && last_direction==UP) && counter<=MAX_STEP]
           caocaodown{{
                         seq[space1]=cc;
                         seq[space2]=cc;
                         space1=space1-12;
                         space2=space2-12;
                         seq[space1]=sp;
           		         seq[space2]=sp;
           		         if (last_move!=cc) counter++;
                         last_move=cc;
                         last_direction=DOWN;
                     }}->CaocaoMove()
           []
           [seq[space1+1]==cc && seq[space2+1]==cc && !(last_move==cc && last_direction==RIGHT) && counter<=MAX_STEP]
           caocaoleft{{
                         seq[space1]=cc;
                         seq[space2]=cc;
                         space1=space1+2;
                         space2=space2+2;
                         seq[space1]=sp;
           		         seq[space2]=sp;
           		         if (last_move!=cc) counter++;
                         last_move=cc;
                         last_direction=LEFT;
                     }}->CaocaoMove()
           []
           [seq[space1-1]==cc && seq[space2-1]==cc && !(last_move==cc && last_direction==LEFT) && counter<=MAX_STEP]
           caocaoright{{
                          seq[space1]=cc;
                          seq[space2]=cc;
                          space1=space1-2;
                          space2=space2-2;
                          seq[space1]=sp;
           		          seq[space2]=sp;
           		          if (last_move!=cc) counter++;
                          last_move=cc;
                          last_direction=RIGHT;
                      }}->CaocaoMove();
                                 
BingMove() = ||x:{{b1..b4}}@Bing(x);
JiangMove() = ||x:{{j5..j9}}@Jiang(x);
Game() = Initial();(BingMove()||JiangMove()||CaocaoMove());


//caocao arrives the exit
#define goal (seq[26]==cc && seq[27]==cc && seq[32]==cc && seq[33]==cc);

//try to find out the best solution
#assert Game() reaches goal with min(counter);
'''
        else:
            raise ValueError("Please enter a valid option!")
    
    elif algo_id == "para_stack":
        try:
            stack_size, num_process = re.split(r'[,\s]+', var_value.strip())
            stack_size = int(stack_size)
            num_process = int(num_process)
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_process < 3) or (stack_size < 1):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        lines = []
        # Header
        lines.append("// stack size")
        lines.append(f"#define SIZE {stack_size};")
        lines.append("")
        lines.append("// shared head pointer for the concrete implementation")
        lines.append("var H = 0;")
        lines.append("")
        lines.append("//////////////// The Concrete Implementation Model //////////////////")
        # Push
        lines.append("Push() = push_inv -> PushLoop(H);")
        lines.append("")
        lines.append("PushLoop(v) = (")
        lines.append("    ifa (v == H) {")
        lines.append("        t{if(H < SIZE) {H = H+1;}} -> push_res.(v+1) -> Process()")
        lines.append("    } else {")
        lines.append("        Push()")
        lines.append("    });")
        lines.append("")
        # Pop
        lines.append("Pop() = pop_inv -> PopLoop(H);")
        lines.append("")
        lines.append("PopLoop(v) =")
        lines.append("    (if(v == 0) {")
        lines.append("        pop_res.0 -> Process() ")
        lines.append("    } else {")
        lines.append("        (ifa(v != H) { Pop() } else {")
        lines.append("            t{H = H-1;} -> pop_res.(v-1) -> Process()")
        lines.append("        })")
        lines.append("    });")
        lines.append("")
        # Process and System
        lines.append("Process() = (Push()[]Pop());")
        lines.append(f"Stack() = (|||{{{num_process}}}@Process());")
        lines.append("")
        # Assertions
        lines.append("#assert Stack() deadlockfree;")
        push_terms = " ||".join(f"push_res.{i}" for i in range(stack_size))
        lines.append(f"#assert Stack() |= [](push_inv -> <>({push_terms}));")
        
        processed_code = "\n".join(lines)

    elif algo_id == "driving_philo":
        try:
            num_philosophers, num_resources = re.split(r'[,\s]+', var_value.strip())
            num_philosophers = int(num_philosophers)
            num_resources = int(num_resources)
        except:
            raise ValueError("Please ensure that you've entered a valid value for each of the three variables, and separated the values by comma or space!")
        if (num_philosophers < 2) or (num_resources < 1):
            raise ValueError("Please ensure that the values you entered adhere to the requirements!")
        
        processed_code = f'''/***************************************************************************************************
The Driving Philosophers is a new synchronization problem in mobile ad-hoc systems. 
In this problem, an unbounded number of driving philosophers (processes) try to access 
a round-about (set of shared resources, organized along a logical ring).   
The process does not release the resources it has occupied until it occupies all the resources it needs.
"enter" and "exit" are separated as two phases.
*****************************************************************************************************/

//the number of philosophers
#define N {num_philosophers}; 
//the number of resources
#define M {num_resources}; 

//the start and end resource of each philosopher
#define ph1_start 0;
#define ph1_end   3;

#define ph2_start 1;
#define ph2_end   2;

//for each i:
//start_end[i*2] indicates the i-th philosopher's start resource
//start_end[i*2+1] indicates the i-th philosopher's end resource 
var start_end[2*N] = [ph1_start,ph1_end,ph2_start,ph2_end];

//pointer[i] indicates the current resource which i-th philosopher needs to enter
var pointer[N]:{{0..M-1}} = [ph1_start,ph2_start];

//-----------------paste the testing data in "data.text" above for convenience-------------------- 

//flag[i*2]==1: the i-th philosopher has done the drive and can exit the resources
//flag[i*2+1]==1: the i-th phiolsopher has entered all the resources it needs and can drive
var flag[2*N]:{{0..1}};
 
//variables for the fairness
var count[N];
var sum;

//resource[k] indicates the current number of phil which enters k-th resource
//this variable is only for testing the mutex. it will NOT appear in any preconditions
var resource[M];

//this variable is only for testing if there is a state that two processes share one resource
var mutex = false;

/***************************************************************************************************
The second part is the modeling of the philosopher.
Assume: 1.Each philosopher needs to enter a finite continuous sequence of resources to drive.
        2.Each philosopher enters the resources which it needs by sequence until its end resource 
          is entered and starts at its start resource.
        3.Each philosopher exits the resources after its driving by sequence and
          starts at its first entered resource.
*****************************************************************************************************/

//Mainly, in this case, every phil has three phases: occupy all the resources->drive->release all the resources
//Simply, here can use "if else" to control the process, but we use "[]" to split the process to 3 subprocesses just for clarity

Philosopher(i)=[count[i]*N <= sum]   // "counter" method is used to ensure the fairness        
               Phil_occupy(i) [] Phil_drive(i) [] Phil_release(i);
           
Phil_occupy(i) =[]k:{{0..M-1}}@Phil_enter(i,k);
Phil_release(i)=[]k:{{0..M-1}}@Phil_exit(i,k);

//i-th philosopher enters the k-th resource
Phil_enter(i,k) = [flag[i*2+1]==0 && flag[i*2]==0 && k==pointer[i]]
                  enter.i.k
                  -> {{                                   //tau event is to update      
                         resource[k]++;
               		     if(k==start_end[i*2+1])
               		     flag[i*2+1]=1;
               		     pointer[i] = (pointer[i]+1)%M;
                     }}
                  -> occupied.i.k
                  -> Philosopher(i);
        
//i-th philosopher drives              
Phil_drive(i) = [flag[i*2]==0 && flag[i*2+1]==1]
                drive.i
                {{
                    flag[i*2] = 1;
                 	sum = sum +1;
                 	count[i] = count[i] + 1; 
                 	if (sum == N){{                        //clear the counter variables after all phils have done once driving 
                 	    sum = 0;                          //otherwise, it will reaches a run time error
                 	    var y;                            //and also, it can speed up the verification
                 	    while(y<N){{
                 	    count[y]=0;
                 	    y=y+1;}}}}
                }}
                -> Philosopher(i);
               
//i-th philosopher exits k-th resource              
Phil_exit(i,k) = [flag[i*2]==1 && k==(start_end[i*2]+start_end[i*2+1]-pointer[i]+1)%M]
                 exit.i.k
                 -> {{
                        resource[k]--;
                        pointer[i]=(pointer[i]-1)%M;
                        if(pointer[i]==start_end[i*2])
        	              {{flag[i*2] = 0;
                           flag[i*2+1]=0;}}
                    }}
                 -> released.i.k
                 -> Philosopher(i);
               
/***************************************************************************************************
The third part is the modeling of the resources.
*****************************************************************************************************/

Res_Phil(i,k) = enter.i.k -> occupied.i.k -> exit.i.k -> released.i.k -> Resource(k);
Resource(k) = []x:{{0..N-1}}@Res_Phil(x,k);

/***************************************************************************************************
The fourth part is the modeling of the system.
*****************************************************************************************************/

Res()  = ||k:{{0..M-1}}@Resource(k);
Phil() = ||x:{{0..N-1}}@Philosopher(x);

College() = Res()||Phil();

Test_mutex = []k:{{0..M-1}}@([resource[k]>1]{{mutex=true}}->Test_mutex);
Implementation = College() || Test_mutex;


/***************************************************************************************************
The fifth part is the analysis of the system.
*****************************************************************************************************/

//DEADLOCK CHECKING.
#assert College() deadlockfree;

//FAIRNESS CHECKING. 
//the aasertion will hold if the system is deadlock free
#assert College() |= []<> drive.0;
#assert College() |= []<> enter.0.0;

//MUTEX CHECKING. 
#define Mutex (mutex==true);
#assert Implementation() reaches Mutex;
//another way to check mutex (whether resource0 reaches mutex)
#define Mutex_resource0 (resource[0]>1);
#assert College() reaches Mutex_resource0;
//INVALID STATE TRANSITIONS CHECKING.
//this is for testing whether our model in PAT is consistent to our modeling in DFA (Details are discussed in report)
#define BadTransition (flag[1] == 0 && flag[0] == 1); //phil0 has done driving but not entered all resources
#assert College reaches BadTransition;
'''

    # elif algo_id == "":
    #     if var_value < 2:
    #         raise ValueError("Please enter a valid number which is at least 2!")
        
    #     processed_code = 

    else:
        raise ValueError("Sorry, this algorithm does not exist in our database yet.")
    
    return processed_code