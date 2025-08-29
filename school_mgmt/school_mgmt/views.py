from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.conf import settings

class AboutView(TemplateView):
    template_name = "school_mgmt/about.html"

class ContactView(TemplateView):
    template_name = 'school_mgmt/contact.html'
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            send_mail(
                f"{subject} - From {name}",
                message,
                email,  # From email
                [settings.DEFAULT_FROM_EMAIL],  # To email (should probably be different)
                fail_silently=False,
            )
            return self.render_to_response(self.get_context_data(success=True))
        except Exception as e:
            print(f"Email failed to send: {e}")  # Check your server logs
            return self.render_to_response(self.get_context_data(error=True))