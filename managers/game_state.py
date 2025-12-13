"""
Game State Manager for SI3LN Game
Handles game state transitions and validation
"""
from constants import (
    STATE_MAIN_MENU,
    STATE_LOGIN,
    STATE_REGISTER,
    STATE_PLAYER_SELECT,
    STATE_LEVEL_SELECT,
    STATE_GAMEPLAY,
    STATE_LEVEL_WIN,
    STATE_GAME_OVER,
    STATE_PROFILE,
    STATE_HELP
)


class GameState:
    """Manages game state transitions and validation"""
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        STATE_MAIN_MENU: [STATE_LOGIN, STATE_PLAYER_SELECT, STATE_HELP],
        STATE_LOGIN: [STATE_MAIN_MENU, STATE_REGISTER, STATE_GAMEPLAY],
        STATE_REGISTER: [STATE_MAIN_MENU, STATE_LOGIN],
        STATE_PLAYER_SELECT: [STATE_MAIN_MENU, STATE_LEVEL_SELECT],
        STATE_LEVEL_SELECT: [STATE_MAIN_MENU, STATE_GAMEPLAY],
        STATE_GAMEPLAY: [STATE_GAME_OVER, STATE_LEVEL_WIN, STATE_MAIN_MENU],
        STATE_LEVEL_WIN: [STATE_GAMEPLAY, STATE_LEVEL_SELECT, STATE_MAIN_MENU],
        STATE_GAME_OVER: [STATE_GAMEPLAY, STATE_LEVEL_SELECT, STATE_MAIN_MENU],
        STATE_PROFILE: [STATE_MAIN_MENU],
        STATE_HELP: [STATE_MAIN_MENU]
    }
    
    def __init__(self, initial_state=STATE_MAIN_MENU):
        """
        Initialize game state manager
        
        Args:
            initial_state: Initial game state
        """
        self.current_state = initial_state
        self.previous_state = None
    
    def change_state(self, new_state):
        """
        Change to a new state with validation
        
        Args:
            new_state: The new state to transition to
            
        Returns:
            bool: True if transition is valid and successful, False otherwise
        """
        if self.is_valid_transition(new_state):
            self.previous_state = self.current_state
            self.current_state = new_state
            return True
        return False
    
    def is_valid_transition(self, new_state):
        """
        Check if a state transition is valid
        
        Args:
            new_state: The state to transition to
            
        Returns:
            bool: True if transition is valid
        """
        if new_state not in self.VALID_TRANSITIONS:
            return False
        
        allowed_states = self.VALID_TRANSITIONS.get(self.current_state, [])
        return new_state in allowed_states
    
    def get_state(self):
        """Get current state"""
        return self.current_state
    
    def get_previous_state(self):
        """Get previous state"""
        return self.previous_state
    
    def reset(self, new_state=STATE_MAIN_MENU):
        """
        Reset state manager to initial state
        
        Args:
            new_state: State to reset to (default: MAIN_MENU)
        """
        self.previous_state = None
        self.current_state = new_state

