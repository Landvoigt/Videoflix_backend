from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user']

    def validate(self, data):
        if self.instance is None:
            if not data.get('name'):
                raise serializers.ValidationError("Name is required!")
            if not data.get('avatar_id'):
                raise serializers.ValidationError("Avatar is required!")
        
        return data