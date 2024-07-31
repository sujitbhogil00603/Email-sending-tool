from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.utils.text import slugify
import logging
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from django.template.loader import render_to_string

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('send_email')
        else:
            return HttpResponse('Invalid login credentials')
    return render(request, 'login.html')

@login_required
def send_email_view(request):
    if request.method == 'POST':
        recipient_email = request.POST['recipient_email']
        email_subject = request.POST['email_subject']
        email_content = request.POST['email_content']
        email_image = request.FILES.get('email_image')
        email_template = request.POST['email_template']  # Get the selected template
        from_email = 'support@adopt.email'
        password = 'hDthqFv1'

        # Save the uploaded image
        if email_image:
            sanitized_name = slugify(email_image.name, allow_unicode=True)
            image_path = default_storage.save(f'images/{sanitized_name}', email_image)
            logging.debug(f"Image saved at: {image_path}")
        else:
            image_path = None

        # Log image path
        logging.debug(f"Image path: {image_path}")

        # Render the appropriate HTML template with the provided content
        if email_template == 'template1':
            html_content = render_to_string('email_template.html', {
                'content': email_content,
                'image_name': sanitized_name if email_image else None,
            })
        else:
            html_content = render_to_string('testing.html', {
                'content': email_content,
                'image_name': sanitized_name if email_image else None,
            })

        # Log HTML content
        logging.debug(f"HTML content: {html_content}")

        # Create the email message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = email_subject
        msg['From'] = from_email
        msg['To'] = recipient_email

        # Create the HTML part
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(html_content, 'html'))

        # Embed the image if present
        if email_image and image_path:
            with default_storage.open(image_path, 'rb') as img:
                img_data = img.read()
                mime_img = MIMEImage(img_data, name=sanitized_name)
                mime_img.add_header('Content-ID', f'<{sanitized_name}>')
                mime_img.add_header('Content-Disposition', 'inline', filename=sanitized_name)
                msg.attach(mime_img)

                # Log MIME image headers
                logging.debug(f"Image Content-Disposition: inline; filename={sanitized_name}")
                logging.debug(f"Image Content-ID: <{sanitized_name}>")
                logging.debug(f"Image attached to email: {mime_img}")

        # Create a secure SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        try:
            with smtplib.SMTP('mail.adopt.email', 587) as server:
                server.starttls(context=context)  # Secure the connection
                server.login(from_email, password)
                server.sendmail(from_email, recipient_email, msg.as_string())
            messages.success(request, 'Email sent successfully!')
            logging.debug("Email sent successfully!")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            messages.error(request, f'Failed to send email: {e}')

    return render(request, 'send_email.html')
