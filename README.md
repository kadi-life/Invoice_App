# Invoice_App
Invoice and Quotation Management System

## Deploying to Render

This guide will help you deploy the Invoice App to Render.

### Prerequisites

1. A Render account (sign up at [render.com](https://render.com))
2. Your project code pushed to a Git repository (GitHub, GitLab, etc.)

### Deployment Steps

1. **Log in to Render**
   - Go to [dashboard.render.com](https://dashboard.render.com) and sign in

2. **Create a New Web Service**
   - Click on "New +" and select "Web Service"
   - Connect your Git repository
   - Select the repository containing your Invoice App

3. **Configure the Web Service**
   - Name: `invoice-app` (or your preferred name)
   - Environment: `Python`
   - Region: Choose the closest to your users
   - Branch: `main` (or your default branch)
   - Build Command: `./build.sh`
   - Start Command: `gunicorn invoice_project.wsgi:application`
   - Plan: Free (or select a paid plan for production use)

4. **Add Environment Variables**
   - Click on "Environment" and add the following variables:
     - `DEBUG`: `False`
     - `SECRET_KEY`: Generate a secure random string
     - `ALLOWED_HOSTS`: `.onrender.com`
     - `PYTHON_VERSION`: `3.11.4`

5. **Database Setup**
   - Create a PostgreSQL database in Render
   - Add the database connection string as `DATABASE_URL` environment variable

6. **Media Storage (Optional)**
   - If you need to store user-uploaded files, set up an S3-compatible storage
   - Add the following environment variables:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_STORAGE_BUCKET_NAME`
     - `AWS_S3_REGION_NAME`
     - `AWS_S3_ENDPOINT_URL`
     - `AWS_S3_CUSTOM_DOMAIN`

7. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy your application
