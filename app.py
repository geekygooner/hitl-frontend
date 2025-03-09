import os
import socket
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from main import check_compliance, policies, document_path, read_word_document  # Import your functions and data
import io
from docx import * # Import the io module
#from bayoo_docx import Document

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
        
        # Read the document
        document_content = read_word_document(document_path)
        
        # Get compliance results and full document content
        results, full_document = check_compliance(document_content, policies)
        session['results'] = results
        session['full_document'] = full_document
        return redirect(url_for('review'))
    return render_template('review_choice.html')

@app.route('/review', methods=['GET', 'POST'])
def review():
    results = session.get('results')
    full_document = session.get('full_document')
    
    if results is None or full_document is None:
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
    return render_template('review.html', 
                          results=review_results, 
                          review_all=session['review_all'], 
                          error=None, 
                          enumerate=enumerate,
                          full_document=full_document)

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

    try:
        # Load the original document
        doc = Document(document_path)
        
        # Iterate through results and add comments
        for result in results:
            highlighted_text = result.get('Highlighted Text')
            explanation = result.get('Explanation')

            if highlighted_text and explanation:
                try:
                    add_comment_to_highlighted_text(doc, highlighted_text, explanation)
                except Exception as e:
                    print(f"Error adding comment for text '{highlighted_text}': {e}")
                    # Continue with other comments even if one fails

        # Save the modified document to an in-memory file
        output_file = io.BytesIO()
        doc.save(output_file)
        output_file.seek(0)

        # Generate the output filename
        original_filename = os.path.basename(document_path)
        output_filename = f"{os.path.splitext(original_filename)[0]}-output.docx"

        return send_file(output_file, as_attachment=True, download_name=output_filename, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    except Exception as e:
        print(f"Error generating document with comments: {e}")
        return f"Error generating document: {str(e)}", 500

def add_comment_to_highlighted_text(doc, highlighted_text, explanation):
    """
    Adds a comment to the first occurrence of highlighted_text in the document.
    Uses run-level commenting instead of paragraph-level.
    """
    for paragraph in doc.paragraphs:
        if highlighted_text in paragraph.text:
            # Find the run that contains the highlighted text
            text_index = paragraph.text.find(highlighted_text)
            current_index = 0
            comment_added = False
            
            # Try to add comment at run level first
            for i, run in enumerate(paragraph.runs):
                run_length = len(run.text)
                run_end_index = current_index + run_length
                
                # Check if this run contains any part of the highlighted text
                if (current_index <= text_index < run_end_index or 
                    text_index <= current_index < text_index + len(highlighted_text)):
                    # Add comment to this run - try different parameter combinations based on error messages
                    try:
                        # First attempt: simplest form with just the text
                        run.add_comment(explanation)
                        comment_added = True
                        print(f"Added comment to run with simple parameters")
                        break
                    except Exception as e1:
                        print(f"Simple comment failed: {e1}")
                        try:
                            # Second attempt: with author and initials
                            run.add_comment(text=explanation, author="AI", initials="AI")
                            comment_added = True
                            print(f"Added comment to run with named parameters")
                            break
                        except Exception as e2:
                            print(f"Named parameters failed: {e2}")
                            try:
                                # Third attempt: with comment_part parameter (from error message)
                                run.add_comment(comment_part=explanation, author="AI", initials="AI")
                                comment_added = True
                                print(f"Added comment with comment_part parameter")
                                break
                            except Exception as e3:
                                print(f"comment_part parameter failed: {e3}")
                                # Continue to next run
                
                current_index = run_end_index
            
            # Fallback: If no run-level comment was added, try document-level comment
            if not comment_added:
                try:
                    # Add a document-level comment
                    doc.add_comment(explanation, author="AI", initials="AI")
                    print(f"Added document-level comment for: {highlighted_text}")
                except Exception as e:
                    print(f"Failed to add document-level comment: {e}")
            
            break  # Only comment the first occurrence of the highlighted text in the document

if __name__ == '__main__':
    #port = find_available_port()
    port = 58046
    print(f"Running the app on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port) 