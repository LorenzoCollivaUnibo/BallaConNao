import random
from aima.search import Problem
from utils import from_state_to_dict, entropy

from naoMove import NaoMove


#NaoMoves divided by the energy and rythm of the single movement
ENERGY_GROUPS = {
    'low': ['4-Arms_opening','5-Union_arms','StandUp', 'Bow', 'Kick', '3-Double_movement', '2-Right_Arm', 'Rotation_foot_RLeg', 'Rotation_foot_LLeg'],
    'medium': ['7-Move_forward','8-Move_backward','9-Diagonal_left', '10-Diagonal_right', 'Rhythm', 'StandUp', 'ComeOn', 'Dab', 'Hands_on_Hips', 'ThrillerSnapSnap'],
    'high': ['AirGuitar', 'BlowKisses', 'Clap', 'DanceMove', 'Glory', 'Joy', 'SprinklerL', 'SprinklerR', 'Wave', 'StandUp', 'FootSteps', 'HeadMove', 'HulaHoop', 'PulpFiction', 'Happy_Birthday', 'TheRobot', 'Shuffle', 'i_alternate', 'i_arm_dance', 'i_finger_face', 'i_head_flex', 'i_one_foot_hand_up', 'ThrillerArmSideways']
}

#Verify if the move nelongs to the specified energy group
def is_in_energy_group(move_name, energy_level):
    return move_name in ENERGY_GROUPS.get(energy_level, [])


#Class that defines the planning problem of the NAO choreography
class NaoProblem(Problem):

    def __init__(self, initial, goal, moves):
        super().__init__(initial, goal)
        self.previous_choreography = []
        self.available_moves = moves
        self.rms_profile = None      # energy profile of the song
        self.initial_entropy = entropy(from_state_to_dict(initial)['choreography'])
        self.initial_time = from_state_to_dict(initial).get('remaining_time', 0.0)

    #returns the musical energy (RMS) at the given time
    def get_music_energy(self, elapsed_time):
        if self.rms_profile is None:
            return 0.2  #default value
        
        times, rms_values = zip(*self.rms_profile)
        #finde the nearest musical frame
        import bisect
        idx = bisect.bisect_left(times, elapsed_time)
        idx = min(idx, len(rms_values) - 1)
        return rms_values[idx]

    #returns a function to check if the move is applicable due to the preconditions, postconditions, the last move and 
    def is_move_applicable(self, state, move_name, move):
        state_dict = from_state_to_dict(state)

        #Is the time sufficient?
        if state_dict['remaining_time'] < move.duration:
            return False

        #The preconditions are respected?
        if 'standing' in move.preconditions:
            if state_dict['standing'] != move.preconditions['standing']:
                return False

        #Let's avoid repeating the same move twice in a row
        last_move = state_dict['choreography'][-1]
        if move_name == last_move:
            return False

        return True # If it passes the basic constraints (time, preconditions, repetition) the move is APPLICABLE.

    #Applicable actions
    def actions(self, state):    

        usable_actions = [
            move_name for move_name, move in self.available_moves.items()
            if self.is_move_applicable(state, move_name, move)
        ]
        print("APPLICABILI FINALI:", usable_actions)
        random.shuffle(usable_actions)


        return usable_actions

    # Result of the action (state transition)
    def result(self, state, action):
        nao_move = self.available_moves[action]
        state_dict = from_state_to_dict(state)

        # Calculate new entropy based on current choreography
        new_choreography = [*state_dict['choreography'], action]
        new_entropy = entropy(new_choreography)

        # Updating "standing" status
        if 'standing' in nao_move.postconditions:
            new_standing = nao_move.postconditions['standing']
        else:
            new_standing = state_dict['standing']

        return (
            ('choreography', tuple(new_choreography)),
            ('standing', new_standing),
            ('remaining_time', state_dict['remaining_time'] - nao_move.duration),
            ('moves_done', state_dict['moves_done'] + 1),
            ('entropy', new_entropy)
        )
    # Test del goal
    def goal_test(self, state):
        state_dict = from_state_to_dict(state)
        goal_dict = from_state_to_dict(self.goal)

        # Main constraints
        moves_done_constraint = (state_dict['moves_done'] >= goal_dict.get('moves_done', 0))
        entropy_constraint = (state_dict.get('entropy', 0) >= goal_dict.get('entropy', 0))
        standing_constraint = (
            goal_dict.get('standing') is None or
            state_dict['standing'] == goal_dict['standing']
        )

        ## Time constraint (not too much beyond the expected duration)
        time_constraint = state_dict['remaining_time'] >= 0.0

        return time_constraint and moves_done_constraint and entropy_constraint and standing_constraint


    # Heuristic function for the A* Search algorithm
    def h(self, node):
        state_dict = from_state_to_dict(node.state)
        
        # Compute the cumulative time and the corresponding music energy level
        # based on all moves performed so far (including previous choreographies).
        prev = list(getattr(self, "previous_choreography", []))
        current = list(state_dict['choreography'])
        full_choreo = prev + current
        
        time_used = sum(
            self.available_moves.get(m, NaoMove(0)).duration
            for m in full_choreo
            if m in self.available_moves
        )
        current_energy = self.get_music_energy(time_used)
        
        # Handle the case where the choreography is empty (root node)
        # In this case, all penalties are zero since no moves have been executed yet.
        if not current:
            last_move_name = None 
            h_music = 0.0
        else:
            # Retrieve the last executed move to evaluate its energy coherence
            last_move_name = state_dict['choreography'][-1]
            
            # 1. Music energy coherence penalty (h_music)
            # This component aligns the intensity of the robot’s movements
            # with the musical energy (RMS) at the current time of the track.
            h_music = 0.0  # Initialization

            # Low-energy move performed during a medium/high-energy moment → strong penalty
            if is_in_energy_group(last_move_name, 'low') and current_energy > 0.3:
                h_music = 3.0
                
            # Medium-energy move during a low-energy moment → mild penalty
            elif is_in_energy_group(last_move_name, 'medium') and current_energy < 0.3:
                h_music = 2.0

            # Medium-energy move during a medium/high-energy moment → small adjustment
            elif is_in_energy_group(last_move_name, 'medium') and current_energy > 0.3:
                h_music = 1.0
            
            # High-energy move performed during a low-energy moment → strong penalty
            elif is_in_energy_group(last_move_name, 'high') and current_energy < 0.3:
                h_music = 4.0
            
        # 2. Entropy-based heuristic (h_entropy)
        # Encourages diversity in the choreography by reducing the heuristic cost
        # when the entropy (variability of moves) is higher.
        h_entropy = - state_dict.get('entropy', 0) * 4.0

        # 3. Move-count heuristic (h_moves)
        # Ensures that a minimum number of moves are executed within each segment.
        # Penalizes nodes that have not yet reached the target number of moves.
        goal_moves_done = from_state_to_dict(self.goal).get('moves_done', 0)
        moves_missing = max(0, goal_moves_done - state_dict['moves_done'])
        h_moves = moves_missing * 10.0

        # 4. Small random perturbation (jitter)
        # Introduces stochastic variation to prevent deterministic patterns
        # and encourage exploration of diverse choreography branches.
        jitter = random.uniform(-0.5, 0.5)

        # Final heuristic value
        # - Prioritizes achieving the required number of moves (h_moves)
        # - Rewards entropy (multiplied by 2.0 to emphasize movement diversity)
        # - Adds penalties for poor music–motion coherence (h_music)
        # - Applies a small random factor to promote variability
        return (
            h_moves                             # Priority: reaching the goal number of moves
            + h_entropy * 2.0                   # Encourage higher entropy (diversity)
            + h_music                           # Penalize musical incoherence
            + jitter                            # Add stochastic variation
        )
