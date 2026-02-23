"""
Score management system for SI3LN Game
Manages high scores and leaderboard (top 20)
"""
import json
import os
from datetime import datetime
from constants import SCORES_FILE


class ScoreManager:
    def __init__(self):
        self.scores = self.load_scores()
        self.max_scores = 20  # Top 20
    
    def load_scores(self):
        """Load scores from JSON file"""
        if os.path.exists(SCORES_FILE):
            try:
                with open(SCORES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading scores: {e}")
                return []
        return []
    
    def save_scores(self):
        """Save scores to JSON file"""
        try:
            with open(SCORES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving scores: {e}")
    
    def add_score(self, username, score, level_reached):
        """
        Add a new score to the leaderboard
        Returns (position, is_top_20) - position is 1-indexed, or None if not in top 20
        """
        # Don't save guest scores
        if not username or username == "Guest":
            return None, False
        
        score_entry = {
            "username": username,
            "score": score,
            "level": level_reached,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to scores
        self.scores.append(score_entry)
        
        # Sort by score (descending)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Keep only top 20
        if len(self.scores) > self.max_scores:
            self.scores = self.scores[:self.max_scores]
        
        # Find position
        position = None
        for i, entry in enumerate(self.scores):
            if (entry["username"] == username and 
                entry["score"] == score and 
                entry["level"] == level_reached):
                position = i + 1
                break
        
        is_top_20 = position is not None
        
        if is_top_20:
            self.save_scores()
        
        return position, is_top_20
    
    def get_top_scores(self, limit=20):
        """Get top N scores"""
        return self.scores[:limit]
    
    def get_user_best_score(self, username):
        """Get user's best score"""
        user_scores = [s for s in self.scores if s["username"] == username]
        if user_scores:
            return max(user_scores, key=lambda x: x["score"])
        return None
    
    def is_high_score(self, score):
        """Check if score would make it to top 20"""
        if len(self.scores) < self.max_scores:
            return True
        return score > self.scores[-1]["score"]
    
    def get_rank(self, score):
        """Get what rank a score would have"""
        rank = 1
        for entry in self.scores:
            if score <= entry["score"]:
                rank += 1
        return rank if rank <= self.max_scores else None
