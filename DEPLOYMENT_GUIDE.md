# Deployment Guide: GitHub and Vercel with Neon Database

## 1. Setting Up GitHub Repository

### Prerequisites
- A [GitHub](https://github.com/) account
- Git installed on your computer

### Steps to Create and Push to GitHub

1. **Create a new repository on GitHub**
   - Go to [GitHub](https://github.com/) and sign in
   - Click the '+' icon in the top right and select 'New repository'
   - Name your repository (e.g., "invoice-app")
   - Choose public or private visibility
   - Click 'Create repository'

2. **Initialize Git in your local project (if not already done)**
   ```bash
   cd c:\Users\KADI-LIFE\Desktop\Invoice_App
   git init
   ```

3. **Add your files to Git**
   ```bash
   git add .
   ```

4. **Commit your files**
   ```bash
   git commit -m "Initial commit"
   ```

5. **Add GitHub as remote repository**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/invoice-app.git
   ```
   (Replace YOUR_USERNAME with your actual GitHub username and invoice-app with your repository name)

6. **Push your code to GitHub**
   ```bash
   git push -u origin main
   ```
   (If your default branch is 'master' instead of 'main', use 'master' instead)

## 2. Deploying to Vercel with Neon Database

### Prerequisites
- A [Vercel](https://vercel.com/) account (you can sign up with your GitHub account)
- A [Neon](https://neon.tech/) account for PostgreSQL database

### Setting Up Neon Database

1. **Create a Neon account**
   - Go to [Neon](https://neon.tech/) and sign up

2. **Create a new project**
   - From the Neon dashboard, click 'New Project'
   - Name your project (e.g., "invoice-app-db")
   - Select a region close to your target audience
   - Click 'Create Project'

3. **Get your database connection string**
   - In your project dashboard, go to the 'Connection Details' tab
   - Copy the connection string (it should look like: `postgres://user:password@endpoint/database`)
   - Save this connection string securely as you'll need it for Vercel deployment

### Deploying to Vercel

1. **Connect Vercel to your GitHub repository**
   - Go to [Vercel](https://vercel.com/) and sign in
   - Click 'Add New...' and select 'Project'
   - Connect to your GitHub account if not already connected
   - Select your invoice-app repository
   - Click 'Import'

2. **Configure project settings**
   - Framework Preset: Select 'Other'
   - Build Command: `./build_files.sh`
   - Output Directory: `staticfiles`
   - Install Command: `pip install -r requirements.txt`

3. **Add environment variables**
   - Scroll down to 'Environment Variables'
   - Add the following variables:
     - `SECRET_KEY`: A secure random string (you can generate one at [https://djecrety.ir/](https://djecrety.ir/))
     - `DEBUG`: Set to 'False' for production
     - `DATABASE_URL`: Your Neon PostgreSQL connection string

4. **Deploy**
   - Click 'Deploy'
   - Wait for the deployment to complete

5. **Run migrations**
   - After deployment, go to the 'Deployments' tab
   - Click on the latest deployment
   - Go to 'Functions' tab
   - Click on 'Logs'
   - Click on 'Run Command'
   - Run: `python manage.py migrate`
   - Then run: `python manage.py createsuperuser` to create an admin user

## 3. Verifying Neon Database Connection

1. **Check your application logs**
   - In Vercel, go to your project dashboard
   - Click on 'Deployments' and select the latest deployment
   - Go to 'Functions' tab and click on 'Logs'
   - Look for any database connection errors

2. **Test database functionality**
   - Visit your deployed application
   - Try to log in with your superuser credentials
   - Create a test invoice or quotation
   - If these operations work, your database connection is successful

3. **Verify in Neon dashboard**
   - Go to your Neon project dashboard
   - Check the 'Connections' tab to see active connections
   - Check the 'Storage' tab to see if data is being stored

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Verify your DATABASE_URL environment variable is correct
   - Check if your IP is allowed in Neon's connection settings
   - Ensure the psycopg2-binary package is in your requirements.txt

2. **Static files not loading**
   - Verify WhiteNoise is properly configured in settings.py
   - Check if collectstatic was run during build

3. **Deployment failures**
   - Check Vercel logs for specific error messages
   - Ensure all required packages are in requirements.txt

### Getting Help

- Vercel Documentation: [https://vercel.com/docs](https://vercel.com/docs)
- Neon Documentation: [https://neon.tech/docs](https://neon.tech/docs)
- Django on Vercel Guide: [https://vercel.com/guides/deploying-django-to-vercel](https://vercel.com/guides/deploying-django-to-vercel)