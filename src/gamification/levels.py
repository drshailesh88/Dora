"""
Level System

100-level progression system with increasing XP requirements and rewards.
"""

from typing import Optional

from .models import Level


# Level tier definitions
LEVEL_TIERS = {
    'intern': (1, 10, 'Medical Intern', '🩺'),
    'junior_resident': (11, 25, 'Junior Resident', '👨‍⚕️'),
    'senior_resident': (26, 40, 'Senior Resident', '👩‍⚕️'),
    'specialist': (41, 60, 'Specialist', '🔬'),
    'senior_specialist': (61, 80, 'Senior Specialist', '⚕️'),
    'expert': (81, 95, 'Expert', '🏆'),
    'master': (96, 100, 'Master Physician', '👑'),
}


class LevelService:
    """Service for managing user levels"""

    def __init__(self, storage):
        """
        Initialize level service.

        Args:
            storage: Storage backend
        """
        self.storage = storage
        self._levels = self._generate_all_levels()

    def get_level(self, level_number: int) -> Optional[Level]:
        """
        Get level definition.

        Args:
            level_number: Level number (1-100)

        Returns:
            Optional[Level]: Level definition or None
        """
        if level_number < 1 or level_number > 100:
            return None

        return self._levels.get(level_number)

    def get_all_levels(self) -> list[Level]:
        """Get all level definitions."""
        return [self._levels[i] for i in range(1, 101)]

    def get_level_for_xp(self, total_xp: int) -> Level:
        """
        Get level for given total XP.

        Args:
            total_xp: Total XP points

        Returns:
            Level: Current level
        """
        current_level = 1

        for level_num in range(1, 101):
            level = self._levels[level_num]
            if total_xp >= level.xp_required:
                current_level = level_num
            else:
                break

        return self._levels[current_level]

    def get_level_progress(self, total_xp: int) -> dict:
        """
        Get detailed level progress.

        Args:
            total_xp: Total XP points

        Returns:
            dict: Level progress information
        """
        current_level_obj = self.get_level_for_xp(total_xp)
        current_level = current_level_obj.level

        # Calculate XP in current level
        xp_current_level = total_xp - current_level_obj.xp_required

        # Get next level
        if current_level < 100:
            next_level_obj = self._levels[current_level + 1]
            xp_to_next_level = next_level_obj.xp_required - total_xp
            xp_for_level = next_level_obj.xp_for_level
        else:
            # Max level
            xp_to_next_level = 0
            xp_for_level = current_level_obj.xp_for_level

        # Calculate tier info
        tier_info = self._get_tier_info(current_level)

        return {
            'current_level': current_level,
            'current_level_name': current_level_obj.name,
            'current_level_title': current_level_obj.title,
            'current_level_icon': current_level_obj.icon,
            'total_xp': total_xp,
            'xp_current_level': xp_current_level,
            'xp_to_next_level': xp_to_next_level,
            'xp_for_level': xp_for_level,
            'progress_percentage': round(
                (xp_current_level / xp_for_level * 100) if xp_for_level > 0 else 100,
                2
            ),
            'tier_name': tier_info['tier_name'],
            'tier_icon': tier_info['tier_icon'],
            'tier_progress': tier_info['tier_progress'],
            'is_max_level': current_level == 100,
        }

    def get_tier_name(self, level: int) -> str:
        """Get tier name for a level."""
        tier_info = self._get_tier_info(level)
        return tier_info['tier_name']

    def _get_tier_info(self, level: int) -> dict:
        """Get tier information for a level."""
        for tier_key, (min_level, max_level, tier_name, tier_icon) in LEVEL_TIERS.items():
            if min_level <= level <= max_level:
                tier_progress = round(
                    ((level - min_level + 1) / (max_level - min_level + 1) * 100),
                    2
                )
                return {
                    'tier_key': tier_key,
                    'tier_name': tier_name,
                    'tier_icon': tier_icon,
                    'tier_min_level': min_level,
                    'tier_max_level': max_level,
                    'tier_progress': tier_progress,
                }

        # Default (shouldn't reach here)
        return {
            'tier_key': 'unknown',
            'tier_name': 'Unknown',
            'tier_icon': '❓',
            'tier_min_level': 1,
            'tier_max_level': 1,
            'tier_progress': 0,
        }

    def _generate_all_levels(self) -> dict[int, Level]:
        """Generate all 100 level definitions."""
        levels = {}

        for level_num in range(1, 101):
            levels[level_num] = self._create_level(level_num)

        return levels

    def _create_level(self, level_num: int) -> Level:
        """Create a single level definition."""
        # Get tier info
        tier_info = self._get_tier_info(level_num)

        # Calculate XP requirements
        # Formula: Exponential growth with smoothing
        # Base: 100 XP for level 1
        # Each level requires ~15% more XP than previous
        if level_num == 1:
            xp_required_total = 0
            xp_for_this_level = 100
        else:
            prev_level = self._levels.get(level_num - 1) if hasattr(self, '_levels') else None
            if prev_level:
                xp_required_total = prev_level.xp_required + prev_level.xp_for_level
            else:
                # Fallback calculation
                xp_required_total = int(100 * (1.15 ** (level_num - 1)))

            # XP for this level (increases with level)
            xp_for_this_level = int(100 * (1.15 ** (level_num - 1)))

        # Create level name
        level_name = f"Level {level_num}"

        # Create title
        title = self._generate_title(level_num, tier_info)

        # Generate reward description
        reward_description = self._generate_reward_description(level_num, tier_info)

        # Generate unlocks
        unlocks = self._generate_unlocks(level_num)

        # Create level
        return Level(
            level=level_num,
            name=level_name,
            title=title,
            xp_required=xp_required_total,
            xp_for_level=xp_for_this_level,
            reward_description=reward_description,
            unlocks=unlocks,
            icon=tier_info['tier_icon'],
            color=self._get_level_color(level_num),
            xp_bonus_multiplier=self._get_xp_bonus(level_num),
            special_abilities=self._generate_special_abilities(level_num),
        )

    def _generate_title(self, level: int, tier_info: dict) -> str:
        """Generate title for a level."""
        tier_name = tier_info['tier_name']

        # Special titles for milestone levels
        if level == 100:
            return "Grand Master Physician"
        elif level == 95:
            return "Legendary Expert"
        elif level == 90:
            return "Master Clinician"
        elif level == 80:
            return "Distinguished Senior Specialist"
        elif level == 75:
            return "Expert Practitioner"
        elif level == 60:
            return "Renowned Specialist"
        elif level == 50:
            return "Accomplished Specialist"
        elif level == 40:
            return "Expert Senior Resident"
        elif level == 30:
            return "Skilled Senior Resident"
        elif level == 25:
            return "Proficient Junior Resident"
        elif level == 20:
            return "Experienced Junior Resident"
        elif level == 10:
            return "Dedicated Medical Intern"
        elif level == 5:
            return "Aspiring Medical Intern"
        else:
            return tier_name

    def _generate_reward_description(self, level: int, tier_info: dict) -> str:
        """Generate reward description for a level."""
        # Milestone levels get special rewards
        milestone_rewards = {
            5: "Unlock Quiz Generator feature",
            10: "Unlock Advanced Search filters",
            15: "Unlock Case Discussion feature",
            20: "Unlock Peer Consultation feature",
            25: "Unlock Custom Learning Paths",
            30: "Unlock Advanced Analytics dashboard",
            35: "Unlock CME Certificate customization",
            40: "Unlock Priority Support",
            50: "Unlock Voice Query advanced features",
            60: "Unlock Premium content library",
            75: "Unlock Expert community access",
            80: "Unlock Conference discount codes",
            90: "Unlock Lifetime premium features",
            100: "Unlock Master Physician exclusive perks",
        }

        if level in milestone_rewards:
            return milestone_rewards[level]

        # Tier-based rewards
        tier_key = tier_info['tier_key']

        tier_rewards = {
            'intern': f"Earn {tier_info['tier_name']} badge",
            'junior_resident': f"Earn {tier_info['tier_name']} badge + Streak freeze token",
            'senior_resident': f"Earn {tier_info['tier_name']} badge + 2 Streak freeze tokens",
            'specialist': f"Earn {tier_info['tier_name']} badge + Premium feature access",
            'senior_specialist': f"Earn {tier_info['tier_name']} badge + Advanced analytics",
            'expert': f"Earn {tier_info['tier_name']} badge + Expert perks",
            'master': f"Earn {tier_info['tier_name']} badge + Master rewards",
        }

        return tier_rewards.get(tier_key, f"Earn Level {level} badge")

    def _generate_unlocks(self, level: int) -> list[str]:
        """Generate feature unlocks for a level."""
        unlocks = []

        # Feature unlocks at specific levels
        unlock_map = {
            1: ["Basic Medical Query"],
            5: ["Quiz Generation"],
            10: ["Advanced Search", "Filters"],
            15: ["Case Discussion"],
            20: ["Peer Consultation"],
            25: ["Custom Learning Paths"],
            30: ["Advanced Analytics"],
            35: ["CME Certificate Customization"],
            40: ["Priority Support"],
            50: ["Voice Query Advanced"],
            60: ["Premium Content Library"],
            75: ["Expert Community"],
            80: ["Conference Discounts"],
            90: ["Lifetime Premium"],
            100: ["Master Physician Perks"],
        }

        return unlock_map.get(level, [])

    def _get_level_color(self, level: int) -> str:
        """Get color for a level."""
        if level >= 96:
            return "#FFD700"  # Gold (Master)
        elif level >= 81:
            return "#E6E6FA"  # Lavender (Expert)
        elif level >= 61:
            return "#DDA0DD"  # Plum (Senior Specialist)
        elif level >= 41:
            return "#87CEEB"  # Sky Blue (Specialist)
        elif level >= 26:
            return "#90EE90"  # Light Green (Senior Resident)
        elif level >= 11:
            return "#F0E68C"  # Khaki (Junior Resident)
        else:
            return "#D3D3D3"  # Light Gray (Intern)

    def _get_xp_bonus(self, level: int) -> float:
        """Get XP bonus multiplier for a level."""
        if level >= 76:
            return 1.15
        elif level >= 51:
            return 1.1
        elif level >= 26:
            return 1.05
        else:
            return 1.0

    def _generate_special_abilities(self, level: int) -> list[str]:
        """Generate special abilities for a level."""
        abilities = []

        # Unlock abilities at specific levels
        if level >= 25:
            abilities.append("Priority query processing")

        if level >= 50:
            abilities.append("Advanced voice commands")

        if level >= 75:
            abilities.append("Expert consultation credits")

        if level >= 90:
            abilities.append("Beta feature access")

        if level >= 100:
            abilities.append("Master physician privileges")

        return abilities


def calculate_xp_for_level(level: int) -> int:
    """
    Calculate total XP required to reach a level.

    Args:
        level: Target level (1-100)

    Returns:
        int: Total XP required
    """
    if level <= 1:
        return 0

    # Use exponential growth formula
    total_xp = 0
    for i in range(1, level):
        xp_for_level = int(100 * (1.15 ** (i - 1)))
        total_xp += xp_for_level

    return total_xp
