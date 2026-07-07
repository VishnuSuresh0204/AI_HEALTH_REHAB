import os
import re

template_dir = r"c:\Users\User\Documents\project26\AI-Based Healthcare\pro\templates"

routes = [
    'login', 'signout', 'register_user', 'register_therapist',
    'admin_home', 'admin_view_therapists', 'admin_therapist_action',
    'admin_view_users', 'admin_user_action', 'admin_view_exercises',
    'admin_add_exercise', 'admin_edit_exercise',
    'therapist_home', 'therapist_view_unassigned_patients',
    'therapist_add_patient', 'therapist_view_patients',
    'therapist_patient_detail', 'therapist_create_plan',
    'therapist_edit_plan_items', 'therapist_view_sessions',
    'therapist_view_session_report', 'therapist_review_report',
    'user_home', 'user_view_plans', 'user_medical_history',
    'user_start_session', 'user_session_tracker', 'user_submit_frame',
    'user_complete_session', 'user_download_report', 'user_view_sessions'
]

def fix_html_files():
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for route in routes:
                    # Fix href="/route" -> href="/route/"
                    content = re.sub(rf'href="/{route}"', rf'href="/{route}/"', content)
                    # Fix href="/route?..." -> href="/route/?..."
                    content = re.sub(rf'href="/{route}\?', rf'href="/{route}/?', content)
                    
                    # Fix action="/route" -> action="/route/"
                    content = re.sub(rf'action="/{route}"', rf'action="/{route}/"', content)
                    # Fix action="/route?..." -> action="/route/?..."
                    content = re.sub(rf'action="/{route}\?', rf'action="/{route}/?', content)

                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed {file_path}")

if __name__ == '__main__':
    fix_html_files()
