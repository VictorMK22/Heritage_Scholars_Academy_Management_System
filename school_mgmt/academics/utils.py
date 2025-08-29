from django.db.models import Q
from django.utils import timezone

def get_class_subjects(class_obj):
    """Get all subjects assigned to a class through any method"""
    direct_subjects = class_obj.subject_set.all()
    teaching_subjects = Subject.objects.filter(
        classteaching__classroom=class_obj
    )
    return (direct_subjects | teaching_subjects).distinct()

def get_subject_classes(subject):
    """Get all classes a subject is assigned to through any method"""
    direct_class = [subject.class_assigned] if subject.class_assigned else []
    teaching_classes = [ct.classroom for ct in subject.classteaching_set.all()]
    return list(set(direct_class + teaching_classes))

def get_subject_teacher(subject):
    """Get the effective teacher for a subject"""
    if subject.teacher:
        return subject.teacher
    
    if subject.class_assigned:
        primary = subject.class_assigned.teaching_assignments.filter(
            is_primary=True
        ).first()
        return primary.teacher if primary else None
    
    return None

def current_academic_year():
    """Returns current academic year in format 'YYYY-YYYY'"""
    now = timezone.now()
    if now.month >= 8:  # August or later = next academic year
        return f"{now.year}-{now.year+1}"
    return f"{now.year-1}-{now.year}"