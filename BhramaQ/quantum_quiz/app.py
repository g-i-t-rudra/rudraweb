from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import random
import os

app = Flask(__name__)
app.secret_key = 'quantum_quiz_secret_key_2024'

# Load questions from JSON file
def load_questions():
    with open('data/questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    # Reset session progress if user returns to home
    session['levels_passed'] = []
    return render_template('index.html')

@app.route('/level')
def level():
    return render_template('level.html')

@app.route('/quiz/<int:level_id>')
def quiz(level_id):
    questions = load_questions()
    level_questions = questions.get(f'level_{level_id}', [])
    
    if not level_questions:
        return redirect(url_for('level'))
    
    # Always shuffle and select up to 8 questions (5 main + 3 extra)
    session['all_questions'] = random.sample(level_questions, min(len(level_questions), 8))
    session['current_questions'] = session['all_questions'][:5]
    session['current_question_index'] = 0
    session['score'] = 0
    session['level_id'] = level_id
    session['extra_questions_used'] = 0
    # Ensure levels_passed is in session
    if 'levels_passed' not in session:
        session['levels_passed'] = []
    
    return render_template('quiz.html', 
                         question=session['current_questions'][0],
                         question_number=1,
                         total_questions=len(session['current_questions']),
                         current_score=0)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    user_answer = data.get('answer')
    current_index = session.get('current_question_index', 0)
    current_questions = session.get('current_questions', [])
    all_questions = session.get('all_questions', [])
    extra_questions_used = session.get('extra_questions_used', 0)
    
    if current_index >= len(current_questions):
        return jsonify({'error': 'No more questions'})
    
    current_question = current_questions[current_index]
    correct_answer = current_question['correct_answer']
    
    # Check if answer is correct
    is_correct = user_answer == correct_answer
    if is_correct:
        session['score'] = session.get('score', 0) + 1
    
    # Move to next question
    session['current_question_index'] = current_index + 1
    
    score = session['score']
    questions_answered = session['current_question_index']
    
    # If after 5 questions, score < 4 and extra questions remain, add up to 3 extra
    if questions_answered >= 5 and score < 4 and extra_questions_used < 3:
        next_extra_index = 5 + extra_questions_used
        if next_extra_index < len(all_questions):
            session['current_questions'].append(all_questions[next_extra_index])
            session['extra_questions_used'] = extra_questions_used + 1
            # Do not end quiz yet, let user answer the extra question
    
    # Recalculate current_questions and extra_questions_used after possible append
    current_questions = session.get('current_questions', [])
    extra_questions_used = session.get('extra_questions_used', 0)
    
    # Quiz ends if:
    # - User has 4 or more points (pass)
    # - All possible questions (max 8) have been attempted
    quiz_done = False
    if score >= 4:
        quiz_done = True
    elif session['current_question_index'] >= len(current_questions):
        quiz_done = True
    
    if quiz_done:
        total_questions = session['current_question_index']
        final_score = session['score']
        percentage = round((final_score / total_questions) * 100, 1) if total_questions > 0 else 0
        # Calculate chocolate reward (1 chocolate per level if passed)
        chocolates_earned = 0
        passed = False
        if final_score >= 4:  # Passing threshold
            chocolates_earned = 1  # 1 chocolate per level
            passed = True
            # Track passed level
            if 'levels_passed' in session:
                if session['level_id'] not in session['levels_passed']:
                    session['levels_passed'].append(session['level_id'])
            else:
                session['levels_passed'] = [session['level_id']]
        return jsonify({
            'completed': True,
            'score': final_score,
            'total': total_questions,
            'percentage': percentage,
            'chocolates_earned': chocolates_earned,
            'passed': passed
        })
    
    # Return next question with live score
    next_question = session['current_questions'][session['current_question_index']]
    return jsonify({
        'completed': False,
        'question': next_question,
        'question_number': session['current_question_index'] + 1,
        'total_questions': len(session['current_questions']),
        'is_correct': is_correct,
        'correct_answer': correct_answer,
        'current_score': session['score'],
        'points_earned': 1 if is_correct else 0
    })

@app.route('/completed')
def completed():
    score = session.get('score', 0)
    total = len(session.get('current_questions', []))
    percentage = round((score / total) * 100, 1) if total > 0 else 0
    level_id = session.get('level_id', 1)
    # Calculate chocolate reward (1 chocolate per level if passed)
    chocolates_earned = 0
    passed = False
    if score >= 4:  # Minimum 4/5 to pass
        chocolates_earned = 1  # 1 chocolate per level
        passed = True
    # Get levels passed for progression
    levels_passed = session.get('levels_passed', [])
    all_levels_completed = all(lvl in levels_passed for lvl in [1, 2, 3])
    return render_template('completed.html', 
                         score=score, 
                         total=total, 
                         percentage=percentage,
                         level_id=level_id,
                         chocolates_earned=chocolates_earned,
                         passed=passed,
                         levels_passed=levels_passed,
                         all_levels_completed=all_levels_completed)

if __name__ == '__main__':
    app.run(debug=True) 