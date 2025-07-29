from flask import Flask, render_template_string, send_from_directory
import os
import re

app = Flask(__name__)

# Automatically locate the HWAL folder relative to app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HWAL_DIR = os.path.join(BASE_DIR, "load.hwal")

# Create HWAL folder if missing
if not os.path.exists(HWAL_DIR):
    os.makedirs(HWAL_DIR)

variables = {}

def find_hwal_file():
    for file in os.listdir(HWAL_DIR):
        if file.endswith(".hwal"):
            return os.path.join(HWAL_DIR, file)
    return None

def parse_hwal(file_path):
    output = []
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

        # Load variables
        for var in re.findall(r'<load var="(.+?)" value="(.+?)" ?/?>', content):
            name, val = var
            try:
                variables[name] = int(val)
            except ValueError:
                variables[name] = val

        # Render string tags with optional expression parsing
        for tag in re.findall(r'<string>(.*?)</string>', content):
            for expr in re.findall(r'{{(.*?)}}', tag):
                try:
                    result = str(eval(expr, {}, variables))
                    tag = tag.replace(f'{{{{{expr}}}}}', result)
                except:
                    tag = tag.replace(f'{{{{{expr}}}}}', "[error]")
            output.append(f"<p>{tag}</p>")

        # Embed media
        for file_name in re.findall(r'<play>(.*?)</play>', content):
            ext = os.path.splitext(file_name)[1].lower()
            if ext == ".mp3":
                tag = f"""<audio controls>
                             <source src="/media/{file_name}" type="audio/mpeg">
                          </audio>"""
            elif ext == ".mp4":
                tag = f"""<video width="640" height="360" controls>
                             <source src="/media/{file_name}" type="video/mp4">
                          </video>"""
            else:
                tag = f"<p>[Unsupported media type: {file_name}]</p>"
            output.append(tag)

        # Add link-button support
        # Internal point links
        for btn in re.findall(r'<button:(.+?)>link=point:(.+?)</button>', content):
            label, target = btn
            button_html = f'<a href="#{target}"><button>{label}</button></a>'
            output.append(button_html)

        # External URL links
        for btn in re.findall(r'<button:(.+?)>link=(https?://.+?)</button>', content):
            label, url = btn
            button_html = f'<a href="{url}" target="_blank"><button>{label}</button></a>'
            output.append(button_html)

    return "\n".join(output)

@app.route("/")
def home():
    hwal_file = find_hwal_file()
    if not hwal_file:
        return "<h2>No .hwal file found in load.hwal/</h2>"
    rendered = parse_hwal(hwal_file)
    return render_template_string(f"""
        <html>
        <head><title>HWAL Viewer</title></head>
        <body>
            {rendered}
        </body>
        </html>
    """)

@app.route("/media/<filename>")
def media(filename):
    return send_from_directory(HWAL_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)
