from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import JSONField
from enum import Enum
import json


class AreaType(models.TextChoices):
    RURAL = 'Rural', 'Rural'
    URBAN = 'Urban', 'Urban'
    MIXED = 'Mixed', 'Mixed'


class MembershipType(models.Model):
    """
    Represents a membership type configuration for a region.
    """
    region = models.CharField(max_length=255, help_text="Name of the region")
    area_type = models.CharField(
        max_length=10,
        choices=AreaType.choices,
        help_text="Type of area: Rural, Urban, or Mixed"
    )
    levels_config = JSONField(
        help_text="For Rural/Urban, an integer for levels; for Mixed, a dict with 'urban' and 'rural' keys"
    )
    payments = JSONField(
        help_text="Array of payment amounts matching the levels"
    )
    is_paying = models.BooleanField(
        default=True,
        help_text="Whether this is a paying membership type (False for indigent)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('region', 'area_type', 'is_paying')
        verbose_name = 'Membership Type'
        verbose_name_plural = 'Membership Types'

    def __str__(self):
        return f"{self.region} - {self.area_type} ({'Paying' if self.is_paying else 'Indigent'})"

    def clean(self):
        super().clean()
        
        # Validate levels_config based on area_type
        if self.area_type in [AreaType.RURAL, AreaType.URBAN]:
            if not isinstance(self.levels_config, int) or self.levels_config < 1:
                raise ValidationError(
                    f"For {self.area_type} area type, levels_config must be a positive integer"
                )
            expected_payments_length = self.levels_config
        else:  # MIXED
            if not isinstance(self.levels_config, dict) or \
               'urban' not in self.levels_config or 'rural' not in self.levels_config:
                raise ValidationError(
                    "For Mixed area type, levels_config must be a dict with 'urban' and 'rural' keys"
                )
            urban_levels = self.levels_config.get('urban', 0)
            rural_levels = self.levels_config.get('rural', 0)
            if not isinstance(urban_levels, int) or not isinstance(rural_levels, int) or \
               urban_levels < 0 or rural_levels < 0 or (urban_levels + rural_levels) < 1:
                raise ValidationError(
                    "For Mixed area type, urban and rural levels must be non-negative integers with at least one level"
                )
            expected_payments_length = urban_levels + rural_levels

        # Validate payments array
        if not isinstance(self.payments, list) or len(self.payments) != expected_payments_length:
            raise ValidationError(
                f"Payments must be an array of length {expected_payments_length} "
                f"matching the total number of levels"
            )
        
        if not all(isinstance(p, (int, float)) and p >= 0 for p in self.payments):
            raise ValidationError("All payment amounts must be non-negative numbers")

    def save(self, *args, **kwargs):
        # Validate before saving
        self.full_clean()
        
        # Save the membership type
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # If this is a new paying membership, create a corresponding indigent membership
        if is_new and self.is_paying:
            self._create_indigent_membership()
    
    def _create_indigent_membership(self):
        """Create a corresponding indigent membership type for the same region and area type."""
        indigent_membership = MembershipType(
            region=self.region,
            area_type=self.area_type,
            levels_config=1,  # Only one level (level 0) for indigent
            payments=[0.0],   # Payment is always 0 for indigent
            is_paying=False
        )
        indigent_membership.save()
    
    def get_payment_amount(self, level_number):
        """
        Get the payment amount for a specific level number.
        
        Args:
            level_number (int): The level number to get payment for
            
        Returns:
            float: The payment amount for the level, or None if not found
        """
        if not self.is_paying and level_number == 0:
            return 0.0
            
        if level_number < 0 or level_number >= len(self.payments):
            return None
            
        return self.payments[level_number]

    @classmethod
    def get_membership_payment(cls, region, area_type, level_number):
        """
        Class method to get payment amount for a membership.
        
        Args:
            region (str): Name of the region
            area_type (str): 'Rural', 'Urban', or 'Mixed'
            level_number (int): The level number
            
        Returns:
            float or None: The payment amount, or None if not found
        """
        try:
            # For indigent (level 0), we need to get the indigent membership
            is_paying = level_number != 0
            
            # For Mixed area type with level_number > 0, we need to determine if it's urban or rural
            if area_type == AreaType.MIXED and is_paying:
                # Get the paying membership to check the levels configuration
                paying_membership = cls.objects.get(
                    region=region,
                    area_type=area_type,
                    is_paying=True
                )
                
                # Determine if the level_number corresponds to urban or rural
                urban_levels = paying_membership.levels_config.get('urban', 0)
                
                if level_number <= urban_levels:
                    area_type = AreaType.URBAN
                else:
                    area_type = AreaType.RURAL
            
            # Get the appropriate membership
            membership = cls.objects.get(
                region=region,
                area_type=area_type,
                is_paying=is_paying
            )
            
            # For paying memberships, adjust the level number for rural areas in Mixed type
            if is_paying and area_type == AreaType.RURAL and 'urban' in getattr(membership, 'levels_config', {}):
                urban_levels = membership.levels_config.get('urban', 0)
                level_number = level_number - urban_levels - 1
            
            return membership.get_payment_amount(level_number)
            
        except cls.DoesNotExist:
            return None
        except Exception as e:
            # Log the error in production
            return None

class Membership(models.Model):
    """
    Represents a membership for an individual or family.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    membership_type = models.ForeignKey(
        MembershipType,
        on_delete=models.PROTECT,
        related_name='memberships',
        help_text="The type of this membership"
    )
    member_name = models.CharField(max_length=255, help_text="Name of the member or family")
    member_id = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the member")
    level = models.PositiveIntegerField(
        default=1,
        help_text="Membership level (1-based index)"
    )
    start_date = models.DateField(help_text="When the membership starts")
    end_date = models.DateField(help_text="When the membership ends")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the membership"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Membership'
        verbose_name_plural = 'Memberships'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member_name} - {self.membership_type} (Level {self.level})"
    
    def get_payment_amount(self):
        """Get the payment amount for this membership's level."""
        return self.membership_type.get_payment_amount(self.level - 1)  # Convert to 0-based index
    
    def is_indigent(self):
        """Check if this is an indigent membership."""
        return not self.membership_type.is_paying
    
    @classmethod
    def create_membership_type(cls, region, area_type, levels_config, payments):
        """
        Helper method to create a new membership type and its corresponding indigent type.
        
        Args:
            region (str): Name of the region
            area_type (str): 'Rural', 'Urban', or 'Mixed'
            levels_config: For Rural/Urban, an integer; for Mixed, a dict with 'urban' and 'rural' keys
            payments (list): List of payment amounts for each level
            
        Returns:
            tuple: (membership_type, indigent_membership_type)
        """
        # Create the paying membership type
        membership_type = MembershipType.objects.create(
            region=region,
            area_type=area_type,
            levels_config=levels_config,
            payments=payments,
            is_paying=True
        )
        
        # The indigent membership type is automatically created by the save() method
        indigent_membership_type = MembershipType.objects.get(
            region=region,
            area_type=area_type,
            is_paying=False
        )
        
        return membership_type, indigent_membership_type

# class InsureeUsers(models.Model):
#     user = 