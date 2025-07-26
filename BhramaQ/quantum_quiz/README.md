# Quantum Quiz

A beautiful, interactive web application for learning quantum physics through engaging quizzes. Explore the fascinating world of quantum mechanics with three progressive difficulty levels.

## Features

- **Three Difficulty Levels**: From basic quantum concepts to advanced applications
- **Interactive Quiz Interface**: Modern, responsive design with real-time feedback
- **Quantum-Themed Design**: Beautiful animations and particle effects
- **Progress Tracking**: Visual progress bars and score tracking
- **Responsive Design**: Works perfectly on desktop and mobile devices

## Project Structure

```
quantum_quiz/
│
├── app.py                 # Main Flask application
├── static/
│   └── style.css         # Quantum-themed CSS styling
├── templates/
│   ├── index.html        # Landing page
│   ├── level.html        # Level selection page
│   ├── quiz.html         # Quiz interface
│   └── completed.html    # Results page
├── data/
│   └── questions.json    # Quiz questions organized by level
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation

1. **Clone or download the project files**

2. **Navigate to the project directory**
   ```bash
   cd quantum_quiz
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser and go to**
   ```
   http://localhost:5000
   ```

## How to Play

1. **Start**: Visit the home page to learn about quantum physics
2. **Choose Level**: Select from three difficulty levels:
   - **Level 1**: Quantum Basics (Beginner)
   - **Level 2**: Advanced Concepts (Intermediate)
   - **Level 3**: Quantum Applications (Advanced)
3. **Take Quiz**: Answer questions about quantum physics concepts
4. **Get Results**: See your score and performance breakdown

## Quiz Levels

### Level 1: Quantum Basics
- Wave-particle duality
- Superposition states
- Quantum measurement
- Heisenberg uncertainty principle

### Level 2: Advanced Concepts
- Quantum entanglement
- Bell's inequality
- Quantum tunneling
- Quantum teleportation

### Level 3: Quantum Applications
- Quantum computing
- Quantum cryptography
- Quantum sensors
- Quantum materials

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Data**: JSON file with structured questions
- **Styling**: Custom quantum-themed CSS with animations
- **Responsive**: Mobile-friendly design

## Customization

### Adding New Questions
Edit `data/questions.json` to add new questions:

```json
{
  "question": "Your question here?",
  "options": [
    "Option A",
    "Option B", 
    "Option C",
    "Option D"
  ],
  "correct_answer": "Option A"
}
```

### Modifying Styles
Edit `static/style.css` to customize the appearance and animations.

### Adding New Levels
1. Add new level data to `questions.json`
2. Update the level selection template
3. Add corresponding routes in `app.py`

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to contribute by:
- Adding new questions
- Improving the design
- Adding new features
- Reporting bugs

## Acknowledgments

- Quantum physics concepts and educational content
- Modern web design principles
- Flask framework for the backend
- CSS animations and effects

---

**Enjoy exploring the quantum realm!** ⚛️ 