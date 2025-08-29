from django.db import migrations

def forwards_func(apps, schema_editor):
    ClassTeaching = apps.get_model('academics', 'ClassTeaching')
    Subject = apps.get_model('academics', 'Subject')
    Teacher = apps.get_model('teachers', 'Teacher')
    
    for subject in Subject.objects.filter(class_assigned__isnull=False):
        # Skip if no class assigned
        if not subject.class_assigned:
            continue
            
        # Find existing assignments for this class
        assignments = ClassTeaching.objects.filter(classroom=subject.class_assigned)
        
        if assignments.exists():
            # Add subject to existing assignments
            for assignment in assignments:
                if subject not in assignment.subjects.all():
                    assignment.subjects.add(subject)
        else:
            # Only create new assignment if at least one teacher exists
            teacher = subject.class_assigned.teachers.first()
            if teacher:
                new_assignment = ClassTeaching.objects.create(
                    classroom=subject.class_assigned,
                    teacher=teacher,
                    is_primary=False
                )
                new_assignment.subjects.add(subject)

def reverse_func(apps, schema_editor):
    """Optional reverse migration"""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0002_classteaching_class_teachers'),
        ('teachers', '0001_initial'),  # Add if teachers app exists
    ]
    
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]