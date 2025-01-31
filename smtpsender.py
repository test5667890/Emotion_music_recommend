# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText

# MY_EMAIL = "ar24son@gmail.com"
# MY_PASSWORD = "eqmdbzdpbyhzntdx"

# def send_welcome_email(receiver_email, fullname):
#     smtp_server = 'smtp.gmail.com'
#     smtp_port = 587
#     sender_email = MY_EMAIL
#     sender_password = MY_PASSWORD

#     # Read the HTML template
#     with open('templates/email_template.html', 'r', encoding='utf-8') as file:
#         html_template = file.read()

#     # Replace the placeholder with the actual recipient's name
#     html_content = html_template.replace('[Recipient\'s Name]', fullname)

#     # Create the welcome email content
#     message = MIMEMultipart()
#     message['From'] = sender_email
#     message['To'] = receiver_email
#     message['Subject'] = 'Welcome to Shopag!'

#     # Attach the HTML content
#     message.attach(MIMEText(html_content, 'html'))

#     try:
#         server = smtplib.SMTP(smtp_server, smtp_port)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.send_message(message)
#         server.quit()
#         print(f'Welcome email sent to {receiver_email}')
#     except Exception as e:
#         print(f'Failed to send welcome email: {e}')


# def send_otp_email(receiver_email, otp):
#     # Set up the SMTP server
#     smtp_server = 'smtp.gmail.com'
#     smtp_port = 587
#     sender_email = MY_EMAIL  # Use your Gmail address
#     sender_password = MY_PASSWORD  # Use your Gmail password or app password

#     # Create the email content
#     message = MIMEMultipart()
#     message['From'] = sender_email
#     message['To'] = receiver_email
#     message['Subject'] = 'Your OTP for Password Reset'
#     body = f"Your OTP for password reset is: {otp}"
#     message.attach(MIMEText(body, 'plain'))

#     try:
#         # Connect to the SMTP server and send the email
#         server = smtplib.SMTP(smtp_server, smtp_port)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.send_message(message)
#         server.quit()
#         print(f'OTP sent to {receiver_email}')
#     except Exception as e:
#         print(f'Failed to send OTP: {e}')

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MY_EMAIL = "ar24son@gmail.com"
MY_PASSWORD = "eqmdbzdpbyhzntdx"

def send_email(receiver_email, subject, html_content):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = MY_EMAIL
    sender_password = MY_PASSWORD

    # Create the email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        print(f'Email sent to {receiver_email}')
    except Exception as e:
        print(f'Failed to send email: {e}')

def send_welcome_email(receiver_email, fullname):
    # Load the email template
    with open('templates/email_templates/email_template.html', 'r') as file:
        html_content = file.read()
    
    # Replace placeholders
    html_content = html_content.replace("[Recipient's Name]", fullname)
    
    # Send the email
    send_email(receiver_email, 'Welcome to Shopag!', html_content)

def send_otp_email(receiver_email, fullname, otp):
    # Load the OTP email template
    with open('templates/email_templates/otp_verification.html', 'r') as file:
        html_content = file.read()
    
    # Replace placeholders
    html_content = html_content.replace("[Recipient's Name]", fullname)
    html_content = html_content.replace("[OTP]", str(otp))
    
    # Send the email
    send_email(receiver_email, 'Your OTP for Verification', html_content)


def send_feedback_email(username, subject, message):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import smtplib

    sender_email = "your_email@example.com"
    receiver_email = "user_email@example.com"  # Use dynamic user email
    password = "your_password"

    # Construct the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Feedback Received"

    body = f"Hi {username},\n\nThank you for your feedback.\n\nSubject: {subject}\nMessage: {message}\n\nBest regards,\nYour Team"
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    except Exception as e:
        print(f"Failed to send feedback email: {e}")
