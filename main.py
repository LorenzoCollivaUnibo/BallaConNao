from aima.search import *
from nao_problem import NaoProblem
from utils import *

import importlib
import brano 

tempo_val = brano.tempo_val
rms = brano.rms
times = brano.times

from naoMove import NaoMove


def main(robot_ip, port):
    # The following ones are the moves made available:
    moves = {
            '4-Arms_opening':               NaoMove(10,  {'standing': True},  {'standing': True}),
            '5-Union_arms':                 NaoMove(7.08,   None,  None),
            '7-Move_forward':               NaoMove(3.1,   {'standing': True},  {'standing': True}),
            '8-Move_backward':              NaoMove(2.8,   {'standing': True},  {'standing': True}),
            '9-Diagonal_left':              NaoMove(2.6,   {'standing': True},  {'standing': True}),
            '10-Diagonal_right':            NaoMove(2.42,   {'standing': True},  {'standing': True}),
            'BlowKisses':                   NaoMove(4.28,   {'standing': True},  {'standing': True}),
            'AirGuitar':                    NaoMove(4.18,   {'standing': True},  {'standing': True}),
            'DanceMove':                    NaoMove(6.16,   {'standing': True},  {'standing': True}),
            'Rhythm':                       NaoMove(3.02,   {'standing': True},  {'standing': True}),
            'SprinklerL':                   NaoMove(4.14,   {'standing': True},  {'standing': True}),
            'SprinklerR':                   NaoMove(4.17,   {'standing': True},  {'standing': True}),
            'StandUp':                      NaoMove(8.31,   {'standing': False}, {'standing': True}),
            'Wave':                         NaoMove(3.72,  None, None),
            'Clap':                         NaoMove(4.13,  None, None),
            'Joy':                          NaoMove(4.39,  None, None),
            'Bow':                          NaoMove(3.86,  {'standing': True}, {'standing': True}),
            'ComeOn':			            NaoMove(3.61, {'standing': True}, {'standing': True}),
            'Dab':			                NaoMove(3.12, {'standing': True}, {'standing': True}),
            'FootSteps':		            NaoMove(7.25, {'standing': True}, {'standing': True}),
            'Hands_on_Hips':   	            NaoMove(1.87, {'standing': True}, {'standing': True}),
            'Happy_Birthday':               NaoMove(9.97, None, None),
            'HeadMove':                     NaoMove(5.40,{'standing': True}, {'standing': True}),
            'HulaHoop':                     NaoMove(4.43, {'standing': True}, {'standing': True}),
            'i_alternate':		            NaoMove(3.90, {'standing': True}, {'standing': True}),
            'i_arm_dance':	                NaoMove(12.44, {'standing': True}, {'standing': True}),
            'i_finger_face':		        NaoMove(5.73, {'standing': True}, {'standing': True}),
            'i_head_flex':		            NaoMove(6.42, {'standing': True}, {'standing': True}),
            'i_one_foot_hand_up': 	        NaoMove(9.49, {'standing': True}, {'standing': True}),
            'Kick':		 	                NaoMove(8.90, {'standing': True}, {'standing': True}),
            'PulpFiction':		            NaoMove(5.63, {'standing': True}, {'standing': True}),
            'Shuffle':			            NaoMove(6.86, {'standing': True}, {'standing': True}),
            'TheRobot':			            NaoMove(6.16, {'standing': True}, {'standing': True}),
            'ThrillerArmSideways':	        NaoMove(5.09, {'standing': True}, {'standing': True}),
            'ThrillerSnapSnap':		        NaoMove(5.08,{'standing': True}, {'standing': True}),
            '3-Double_movement': 	        NaoMove(6.71, None, None),
            '2-Right_Arm': 		            NaoMove(10.12, None, None),
            'Rotation_foot_RLeg':  	        NaoMove(11.51,{'standing': True}, {'standing': True}),
            }

    # The following is the order we chose for the mandatory positions:
    startingPosition = ('14-StandInit',    NaoMove(1.14))
    Mandatory = [('Hello',        NaoMove(4.38)),
                     ('11-Stand',     NaoMove(1.74), None, {'standing': True}),
                     ('WipeForehead', NaoMove(4.6)),
                     ('16-Sit',       NaoMove(19), None, {'standing': False}),
                     ('15-StandZero',  NaoMove(1.9)),
                     ('17-SitRelax',  NaoMove(20), None, {'standing': False})]
    Final_pos = ('6-Crouch',     NaoMove(2))
    pos_list = [startingPosition, *Mandatory, Final_pos]
    Steps_num = len(pos_list) - 1

    # Here we compute the total time lost during the
    # entire choreography for the execution of mandatory moves
    total_time = 0.0
    for pos in pos_list:
        total_time += pos[1].duration
    # We consider 'total_time' as being
    # evenly spread over each planning step:
    mean_time_for_mandatory = total_time / Steps_num

    # Planning phase of the algorithm
    solution = tuple()
    print("PLANNED CHOREOGRAPHY:")
    start_planning = time.time()
    for i in range(1, len(pos_list)):
        # The planning is done in several distinct steps: each
        # one of them consists in solving a tree search in the space
        # of possible choreographies between a mandatory position
        # and the next one.
        starting_pos = pos_list[i - 1]
        ending_pos = pos_list[i]

        choreography = (starting_pos[0],)
        #first move is StandInit as required
        
        initial_standing = postcondition_standing(starting_pos[0])

        #No mandatory positions with preconditions standing = False
        goal_standing = True

        #verify pre and post conditions
        durata_tot_canzone = 136.0
        tempo_obbligatorio_tot = sum(pos[1].duration for pos in pos_list)
        tempo_mosse_libere = max(0, durata_tot_canzone - tempo_obbligatorio_tot)
        print(tempo_mosse_libere)
        remaining_time = tempo_mosse_libere / Steps_num
        print(remaining_time)
        print("Tempo rimanente: ", remaining_time)

        #current state
        cur_state = (('choreography', choreography),
                     ('standing', initial_standing),
                     ('remaining_time', remaining_time),
                     ('moves_done', 0),
                     ('entropy', 0.0))
                     
       
        #Goal state
        cur_goal_state = (('standing', goal_standing),
                        ('remaining_time', 0),  
                        ('moves_done', 2),  
                        ('entropy', 0.5 + 0.1 * (i - 1))) 

        #Find the state solution
        cur_problem = NaoProblem(cur_state, cur_goal_state, moves)
        cur_problem.previous_choreography = solution

        #Music parameters
        cur_problem.tempo_val = tempo_val
        cur_problem.rms_profile = list(zip(times, rms))


        # The partial solution is found using an A* Search algorithm.
        # The full choreography built so far ('solution') is passed to the NaoProblem class
        # so that the evaluation of each new sequence considers the entire performance context.
        #
        # The heuristic function combines three complementary aspects:
        #  - Entropy: encourages movement diversity by favoring choreographies with higher variability.
        #  - Remaining time: penalizes solutions that exceed the available duration of the song.
        #  - Musical energy: aligns the robot’s motion intensity with the current RMS energy level of the track.
        #
        # This integrated approach allows the planner to generate choreographies
        # that are rhythmically consistent, time-balanced, and visually varied throughout the dance.
        cur_solution = astar_search(cur_problem)        
        if cur_solution is None:
            raise RuntimeError(f'Step {i} - no solution was found!')

        cur_solution_dict = from_state_to_dict(cur_solution.state)
        cur_choreography = cur_solution_dict['choreography']
        print(f"Step {i}: \t" + ", ".join(cur_choreography))
        solution += cur_choreography

    end_planning = time.time()
    solution += (Final_pos[0],)
    state_dict = from_state_to_dict(cur_solution.state)
    print("\nSTATISTICS:")
    print(f"Time required by the planning phase: %.2f seconds." % (end_planning-start_planning))
    print(f"Entropy of the solution found: {state_dict['entropy']}")
    print(f"Estimated choreography duration: {136.0 - state_dict['remaining_time']}")
    print("-------------------------------------------------------")
    
    # Dance execution
    print("\nDANCE EXEC:")
    play_song("MUEVELOU.mp3")
    start = time.time()
    do_moves(solution, robot_ip, port)
    end = time.time()
    print("Length of the entire choreography: %.2f seconds." % (end-start))

def postcondition_standing(position):
    if position in ('16-Sit', '17-SitRelax'):
        # In our case, this two moves are the only ones
        # that finish in a 'standing' == False state.
        return False
    return True

if __name__ == "__main__":

    robot_ip = "127.0.0.1"
    port = 9559  # Insert NAO port
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
        robot_ip = sys.argv[1]
    elif len(sys.argv) == 2:
        robot_ip = sys.argv[1]
    
    main(robot_ip, port)
