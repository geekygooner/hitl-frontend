import os
import socket
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from main import check_compliance, policies, project_document  # Import your functions and data
import io  # Import the io module

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for using session

def find_available_port():
    """Finds an available port on the system."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 0))  # Bind to all interfaces on a dynamic port
    port = sock.getsockname()[1]
    sock.close()
    return port

@app.route('/', methods=['GET', 'POST'])
def review_choice():
    if request.method == 'POST':
        session['review_all'] = request.form.get('review_choice') == 'all'
        results = check_compliance(project_document, policies)
        session['results'] = results
        return redirect(url_for('review'))
    return render_template('review_choice.html')

@app.route('/review', methods=['GET', 'POST'])
def review():
    results = session.get('results')
    if results is None:
        return redirect(url_for('review_choice'))

    if request.method == 'POST':
        human_approved_answers = {}
        comments = {}
        all_answered = True
        for i, result in enumerate(results):
            if session['review_all'] or result.get('Flagged', False):
                answer = request.form.get(f'answer_{i}')
                comment = request.form.get(f'comment_{i}', '')  # Default to empty string if no comment
                if not answer:
                    all_answered = False
                    break
                human_approved_answers[i] = answer
                comments[i] = comment

        if all_answered:
            for i, result in enumerate(results):
                if i in human_approved_answers:
                    result['Human Approved Answer'] = human_approved_answers[i]
                    result['Comment'] = comments[i]
                else:
                    result['Human Approved Answer'] = result['Answer']
                    result['Comment'] = ''  # No comment if not reviewed
            session['results'] = results
            return redirect(url_for('results'))
        else:
            error = "Please answer all required questions."
            return render_template('review.html', results=results, review_all=session['review_all'], error=error)

    # Filter results based on review choice
    review_results = [result for result in results if session['review_all'] or result.get('Flagged', False)]
    return render_template('review.html', results=review_results, review_all=session['review_all'], error=None, enumerate=enumerate)

@app.route('/results')
def results():
    results = session.get('results')
    if results is None:
        return redirect(url_for('review_choice'))

    return render_template('results.html', results=results)

@app.route('/download_report')
def download_report():
    results = session.get('results')
    if results is None:
        return redirect(url_for('review_choice'))

    report = generate_report(results)
    # Use BytesIO to create an in-memory binary file
    report_file = io.BytesIO()
    report_file.write(report.encode('utf-8'))  # Encode the string to bytes
    report_file.seek(0)  # Reset the file pointer to the beginning
    return send_file(report_file, as_attachment=True, download_name='compliance_report.txt', mimetype='text/plain')

def generate_report(results):
    report = "Final Compliance Report:\n"
    for result in results:
        report += f"Policy: {result['Policy']}\n"
        if "Error" in result:
            report += f"  Error: {result['Error']}\n"
        else:
            report += f"  AI Answer: {result.get('Answer', 'N/A')}\n"
            report += f"  Explanation: {result.get('Explanation', 'N/A')}\n"
            report += f"  Highlighted Text: {result.get('Highlighted Text', 'N/A')}\n"
            report += f"  Human Approved Answer: {result.get('Human Approved Answer', 'N/A')}\n"
            report += f"  Comment: {result.get('Comment', 'N/A')}\n"
        report += "-" * 40 + "\n"
    return report

if __name__ == '__main__':
    #port = find_available_port()
    port = 58046
    print(f"Running the app on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port) 