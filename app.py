from flask import Flask, request, render_template, send_file, redirect, url_for, flash
from PyPDF2 import PdfMerger
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
MERGED_FOLDER = 'merged'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MERGED_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Simple in-memory merge counter per IP per day
merge_counter = {}

def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

def can_merge(ip, plan):
    today = datetime.now().strftime('%Y-%m-%d')
    if ip not in merge_counter or merge_counter[ip]['date'] != today:
        merge_counter[ip] = {'date': today, 'count': 0}
    if plan == 'free' and merge_counter[ip]['count'] >= 2:  # changed from 5 to 2
        return False
    return True

def increment_merge(ip):
    merge_counter[ip]['count'] += 1

@app.route('/', methods=['GET', 'POST'])
def index():
    merged = False
    plan = request.args.get('plan', 'free')  # 'free' or 'pro'
    ip = get_client_ip()
    if request.method == 'POST':
        # Plan check
        if not can_merge(ip, plan):
            flash('Free plan limit reached. Upgrade to Pro for unlimited merges.', 'danger')
            return render_template('index.html', merged=False, plan=plan)
        files = request.files.getlist('pdfs')
        pdf_paths = []
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                pdf_paths.append(path)
        if pdf_paths:
            merged_path = os.path.join(MERGED_FOLDER, 'merged.pdf')
            # Remove previous merged file if exists
            if os.path.exists(merged_path):
                os.remove(merged_path)
            try:
                merger = PdfMerger()
                for pdf in pdf_paths:
                    try:
                        merger.append(pdf)
                    except Exception as e:
                        flash(f'Error merging {os.path.basename(pdf)}: {str(e)}', 'danger')
                merger.write(merged_path)
                merger.close()
                for pdf in pdf_paths:
                    os.remove(pdf)
                if os.path.exists(merged_path):
                    increment_merge(ip)
                    flash('PDFs merged successfully!', 'success')
                    merged = True
                else:
                    flash('Failed to merge PDFs.', 'danger')
            except Exception as e:
                flash(f'Error during merging: {str(e)}', 'danger')
        else:
            flash('Please upload at least one PDF file.', 'danger')
    return render_template('index.html', merged=merged, plan=plan)

@app.route('/download')
def download_file():
    merged_path = os.path.join(MERGED_FOLDER, 'merged.pdf')
    if os.path.exists(merged_path):
        return send_file(merged_path, as_attachment=True)
    else:
        flash('No merged PDF found. Please merge files first.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
