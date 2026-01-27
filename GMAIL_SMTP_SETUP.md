# 📧 Gmail SMTP Setup Guide for OTP Email Sending

## ✅ Current Status
- ✅ Code configured to send emails via Gmail SMTP
- ✅ Email: subrahmanyam310308@gmail.com
- ⚠️ **Action Required**: Generate Gmail App Password

---

## 🔑 Step-by-Step: Generate Gmail App Password

### Step 1: Enable 2-Step Verification
1. Go to **Google Account**: https://myaccount.google.com/security
2. Scroll down to **"How you sign in to Google"**
3. Click on **"2-Step Verification"**
4. Follow the setup instructions if not already enabled

### Step 2: Generate App Password
1. After enabling 2FA, go to: https://myaccount.google.com/apppasswords
   - Or search for "App passwords" in Google Account settings
2. You might need to sign in again
3. Under "Select app", choose **"Mail"**
4. Under "Select device", choose **"Windows Computer"**
5. Click **"Generate"**
6. A 16-character password will appear (format: `xxxx xxxx xxxx xxxx`)
7. **Copy this password immediately** (you won't see it again)

### Step 3: Update .env File
1. Open: `backend\.env`
2. Find the line: `SMTP_PASSWORD=your_16_character_app_password_here`
3. Replace with your generated password (remove spaces):
   ```
   SMTP_PASSWORD=abcdabcdabcdabcd
   ```
4. Save the file

### Step 4: Restart Backend Server
Stop and restart your backend server to load the new configuration:
```bash
# Press Ctrl+C to stop the current server
# Then restart:
cd backend
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing Email Sending

After configuration, test the OTP email:

1. Go to the frontend registration page: http://localhost:3000/register
2. Enter your email and other details
3. Click "Register"
4. Check your email inbox for the OTP code
5. Enter the OTP on the verification screen

---

## 📋 Email Features Configured

✅ **Professional HTML Email Design**
- Branded with NeuroWellCA logo
- Centered OTP code in styled box
- Mobile-responsive design
- Plain text fallback for older email clients

✅ **Security Features**
- 6-digit OTP code
- 5-minute expiration
- Secure SMTP with TLS encryption

✅ **Fallback Behavior**
- If SMTP not configured: OTP printed to console
- If SMTP fails: OTP printed to console (registration still works)
- Graceful error handling with detailed logging

---

## 🔍 Troubleshooting

### Issue: "SMTP Authentication Failed"
**Solution**: 
- Double-check your App Password (no spaces)
- Ensure 2-Step Verification is enabled
- Generate a new App Password if needed

### Issue: "Connection refused"
**Solution**:
- Check your internet connection
- Verify Gmail SMTP server is accessible
- Try: `telnet smtp.gmail.com 587`

### Issue: Email not received
**Check**:
1. Spam/Junk folder
2. Backend console for OTP code (fallback)
3. Email address spelling
4. Gmail account not blocked

---

## 📝 Configuration Details

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=subrahmanyam310308@gmail.com
SMTP_PASSWORD=your_16_character_app_password_here
SMTP_FROM_NAME=NeuroWellCA
```

---

## 🔒 Security Notes

1. **Never commit** the `.env` file with real passwords to Git
2. The App Password is **different** from your Gmail password
3. App Passwords can be **revoked** anytime from your Google Account
4. Each app/device should have its own App Password
5. If compromised, revoke and generate a new one immediately

---

## 📧 Email Preview

**Subject**: 🧠 NeuroWellCA - Email Verification Code

**Body**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 NeuroWellCA
Email Verification

Your verification code is:

╔═══════════════╗
║   123456      ║
╚═══════════════╝

This code expires in 5 minutes.

If you didn't request this code, 
please ignore this email.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NeuroWellCA - AI-Powered Mental 
Health Support Platform
```

---

## ✅ Next Steps

1. [ ] Generate Gmail App Password
2. [ ] Update `backend\.env` with the password
3. [ ] Restart backend server
4. [ ] Test registration with real email
5. [ ] Verify email is received

---

**Questions?** Check the backend console logs for detailed error messages.

**Need help?** The system will print the OTP to console as fallback until SMTP is configured.
