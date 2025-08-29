from rest_framework import serializers
from .models import Class, Assignment

class ClassSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    
    class Meta:
        model = Class
        fields = ['id', 'name', 'teacher', 'teacher_name']

class AssignmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    class_name = serializers.CharField(source='class_assigned.name', read_only=True)
    is_past_due = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'subject', 'subject_name', 
                 'class_assigned', 'class_name', 'due_date', 'is_past_due', 
                 'points', 'attachment']