import resend
from app.core.config import settings


class EmailService:
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    def send_otp(self, to_email: str, full_name: str, otp: str) -> bool:
        try:
            resend.Emails.send({
                "from": "InterviewAI <onboarding@resend.dev>",
                "to": [to_email],
                "subject": "Verify your InterviewAI account",
                "html": f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:480px;margin:40px auto;background:#1a1a2e;border:1px solid #2d2d44;border-radius:16px;overflow:hidden;">
    <div style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px;text-align:center;">
      <h1 style="margin:0;color:#fff;font-size:24px;font-weight:800;">InterviewAI</h1>
      <p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:14px;">Your AI Interview Coach</p>
    </div>
    <div style="padding:32px;">
      <p style="color:#e2e8f0;font-size:16px;margin:0 0 8px;">Hi {full_name},</p>
      <p style="color:#94a3b8;font-size:14px;margin:0 0 32px;">Enter this code to verify your email address. It expires in 10 minutes.</p>
      <div style="background:#0f0f1a;border:1px solid #2d2d44;border-radius:12px;padding:24px;text-align:center;margin-bottom:32px;">
        <p style="margin:0 0 8px;color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:2px;">Verification Code</p>
        <p style="margin:0;color:#818cf8;font-size:42px;font-weight:900;letter-spacing:12px;">{otp}</p>
      </div>
      <p style="color:#64748b;font-size:12px;margin:0;text-align:center;">If you didn't create an account, you can safely ignore this email.</p>
    </div>
  </div>
</body>
</html>
                """,
            })
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False


email_service = EmailService()