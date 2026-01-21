"""
LLM Reporter - Generate AI scouting reports using Qwen3-4B.

Uses HuggingFace transformers to generate natural language
interpretations of video analysis results.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMReporter:
    """
    Generate AI scouting reports using Qwen3-4B.
    
    Falls back to template-based generation if model not available.
    """
    
    def __init__(self, model_name: str = "Qwen/Qwen3-4B", use_template_only: bool = False):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self._use_fallback = use_template_only  # Skip LLM if True
        
    def _load_model(self):
        """Lazy load the LLM model."""
        if self._loaded or self._use_fallback:
            return
        
        self._loaded = True
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"Loading LLM: {self.model_name}")
            
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
            
            logger.info("LLM loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not load LLM ({e}), using template fallback")
            self._use_fallback = True
    
    def generate_scouting_report(
        self,
        home_team: str,
        away_team: str,
        vision_score: float,
        audio_energy: float,
        flow_stats: dict,
        peak_visual_moment: str,
        peak_audio_moment: str
    ) -> str:
        """
        Generate a natural language scouting report.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            vision_score: Overall visual dominance (0-1)
            audio_energy: Overall crowd energy (0-1)
            flow_stats: {mean_flow, max_flow, burstiness}
            peak_visual_moment: Timestamp of highest visual score
            peak_audio_moment: Timestamp of highest audio energy
        
        Returns:
            AI-generated scouting report string
        """
        self._load_model()
        
        if self._use_fallback:
            return self._generate_template_report(
                home_team, away_team, vision_score, audio_energy,
                flow_stats, peak_visual_moment, peak_audio_moment
            )
        
        # Build prompt for LLM
        prompt = self._build_prompt(
            home_team, away_team, vision_score, audio_energy,
            flow_stats, peak_visual_moment, peak_audio_moment
        )
        
        try:
            inputs = self._tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
            
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id
            )
            
            response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the generated part
            if prompt in response:
                response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_template_report(
                home_team, away_team, vision_score, audio_energy,
                flow_stats, peak_visual_moment, peak_audio_moment
            )
    
    def _build_prompt(
        self,
        home_team: str,
        away_team: str,
        vision_score: float,
        audio_energy: float,
        flow_stats: dict,
        peak_visual_moment: str,
        peak_audio_moment: str
    ) -> str:
        """Build the prompt for the LLM."""
        return f"""You are an NBA analyst providing a scouting report based on video analysis data.

Game: {away_team} @ {home_team}

Analysis Results:
- Visual Dominance Score: {vision_score:.1%} (higher = home team dominated visually)
- Crowd Energy: {audio_energy:.1%}
- Game Intensity: {flow_stats.get('mean_flow', 0):.2f} (optical flow)
- Burstiness: {flow_stats.get('burstiness', 1):.1f}x (indicates action variance)
- Peak Visual Moment: {peak_visual_moment}
- Peak Crowd Roar: {peak_audio_moment}

Write a 2-3 sentence professional scouting report summarizing these insights. Focus on what the numbers tell us about the game flow and team performance. Be specific and analytical.

Scouting Report:"""
    
    def _generate_template_report(
        self,
        home_team: str,
        away_team: str,
        vision_score: float,
        audio_energy: float,
        flow_stats: dict,
        peak_visual_moment: str,
        peak_audio_moment: str
    ) -> str:
        """Fallback template-based report generation."""
        
        # Determine dominance
        if vision_score > 0.6:
            dominance = f"{home_team} showed clear visual dominance"
        elif vision_score < 0.4:
            dominance = f"{away_team} controlled the visual narrative"
        else:
            dominance = "Neither team established clear visual dominance"
        
        # Crowd energy analysis
        if audio_energy > 0.7:
            crowd = "with explosive crowd energy throughout"
        elif audio_energy > 0.5:
            crowd = "with moderate crowd engagement"
        else:
            crowd = "in a somewhat subdued atmosphere"
        
        # Intensity analysis
        burstiness = flow_stats.get("burstiness", 1.0)
        if burstiness > 2.0:
            intensity = "The game featured high-variance action with dramatic momentum swings."
        elif burstiness > 1.5:
            intensity = "Multiple key runs defined the game's rhythm."
        else:
            intensity = "The game maintained a steady pace throughout."
        
        # Peak moments
        moments = f"Peak visual dominance occurred around {peak_visual_moment}, while the crowd reached its loudest at {peak_audio_moment}."
        
        return f"{dominance} {crowd}. {intensity} {moments}"
    
    def generate_interpretation(self, metric_name: str, value: float) -> str:
        """Generate a short interpretation for a single metric."""
        
        interpretations = {
            "vision": {
                0.8: "Dominant paint presence and shot selection",
                0.6: "Above-average visual execution",
                0.4: "Mixed visual performance",
                0.2: "Struggled with shot selection",
                0.0: "Poor visual indicators throughout"
            },
            "audio": {
                0.8: "Electric arena atmosphere",
                0.6: "Strong crowd engagement",
                0.4: "Moderate energy levels",
                0.2: "Subdued crowd presence",
                0.0: "Minimal crowd factor"
            },
            "flow": {
                3.0: "Extremely high-paced action",
                2.0: "Above-average intensity",
                1.0: "Standard game tempo",
                0.5: "Below-average movement",
                0.0: "Low-intensity contest"
            }
        }
        
        if metric_name not in interpretations:
            return ""
        
        thresholds = interpretations[metric_name]
        for threshold in sorted(thresholds.keys(), reverse=True):
            if value >= threshold:
                return thresholds[threshold]
        
        return thresholds[min(thresholds.keys())]


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    reporter = LLMReporter()
    
    report = reporter.generate_scouting_report(
        home_team="Boston Celtics",
        away_team="New York Knicks",
        vision_score=0.72,
        audio_energy=0.68,
        flow_stats={"mean_flow": 2.34, "max_flow": 8.91, "burstiness": 1.8},
        peak_visual_moment="2:30",
        peak_audio_moment="4:15"
    )
    
    print("Generated Report:")
    print(report)
