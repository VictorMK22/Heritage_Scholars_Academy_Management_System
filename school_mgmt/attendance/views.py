from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from students.models import Student
from .models import Attendance
from .forms import AttendanceForm

class AttendanceListView(ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    paginate_by = 20

    def get_queryset(self):
        return Attendance.objects.all().order_by('-date')

def take_attendance(request):
    if request.method == 'POST':
        date = request.POST.get('date', timezone.now().date())
        students = Student.objects.all()
        
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Absent')
            Attendance.objects.create(
                student=student,
                date=date,
                status=status
            )
        messages.success(request, 'Attendance recorded successfully!')
        return redirect('attendance:list')
    
    students = Student.objects.all()
    return render(request, 'attendance/take_attendance.html', {'students': students})

class AttendanceUpdateView(UpdateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/attendance_form.html'
    success_url = reverse_lazy('attendance:list')

    def form_valid(self, form):
        messages.success(self.request, 'Attendance updated successfully!')
        return super().form_valid(form)

class AttendanceDeleteView(DeleteView):
    model = Attendance
    template_name = 'attendance/attendance_confirm_delete.html'
    success_url = reverse_lazy('attendance:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Attendance record deleted successfully!')
        return super().delete(request, *args, **kwargs)