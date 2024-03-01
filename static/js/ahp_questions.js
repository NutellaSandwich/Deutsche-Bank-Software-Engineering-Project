const questionContainer = document.getElementById("question-container");
const questionText = document.getElementById("question");
const answerBtns = document.getElementById("ans-btns");
const prevBtn = document.getElementById("prev-btn");
const submitBtn = document.getElementById("submit-btn");
const controls = document.getElementById("controls");
// get id here

const more = 3 // value for factors rated more significant
const less = 1/3 // value for factors rated less significant
const same = 1 // value for factors rated equally significant

let matrix = new Array(6).fill(0).map(() => new Array(6).fill(0));

for (index = 0; index < matrix.length; index++) { // factors compared against themselves have val 1
    matrix[index][index] = 1;
}

let lastQuestionStack = [];
let matrixStack = [];

let questionNum = 0;

const factors = ["Size and experience level of team", "Satisfiability with work environment and project scope",
"Project budget", "Efficient time management and weekly hours of work","Quality of code and Git pull requests",
"Frequency and effectiveness of communication within team and with stakeholders"];

const questions = [
    {
        question: 'Which aspect do you value more in your team project?',
        answers: [
            {text: "Size and experience level of team"}, // 1 > 2
            {text: "Satisfiability with work environment and project scope"},
            {text: "Both Equally"}
        ]
    },
    { // 3 > 1 > 2
        question: 'Which aspect do you value more in your team project?',
        answers: [
            {text: "Size and experience level of team"}, // 1 < 3
            {text: "Project budget"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Size and experience level of team"},
            {text: "Quality of code and Git pull requests"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Size and experience level of team"},
            {text: "Frequency and effectiveness of communication within team and with stakeholders"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Size and experience level of team"},
            {text: "Efficient time management and weekly hours of work"},
            {text: 'Both Equally'}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Satisfiability with work environment and project scope"},
            {text: "Efficient time management and weekly hours of work"},
            {text: "Both Equally"}
        ]
    },
    { // should be 3 > 2 so matrix[1][2]  = 1/3 and matrix[2][1] = 3 should be filled
        question: 'Which aspect do you value more in your team project?',
        answers: [
            {text: "Satisfiability with work environment and project scope"}, // 2
            {text: "Project budget"}, // 3
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Satisfiability with work environment and project scope"},
            {text: "Quality of code and Git pull requests"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Satisfiability with work environment and project scope"},
            {text: "Frequency and effectiveness of communication within team and with stakeholders"},
            {text: "Both Equally"}
        ]
    },

    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Project budget"},
            {text: "Efficient time management and weekly hours of work"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Project budget"},
            {text: "Frequency and effectiveness of communication within team and with stakeholders"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Project budget"},
            {text: "Quality of code and Git pull requests"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Efficient time management and weekly hours of work"},
            {text: "Quality of code and Git pull requests"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Efficient time management and weekly hours of work"},
            {text: "Frequency and effectiveness of communication within team and with stakeholders"},
            {text: "Both Equally"}
        ]
    },
    {
        question: "Which aspect do you value more in your team project?",
        answers: [
            {text: "Quality of code and Git pull requests"},
            {text: "Frequency and effectiveness of communication within team and with stakeholders"},
            {text: "Both Equally"}
        ]
    }
]

nextQuestion(false);

function flash(message, type) {
    let messageBox = $("#messageBox");

    messageBox.append("<div class=\"flashedMessage "+type+"\">" + message + "</div>");
}

prevBtn.addEventListener("click", () => {
    if (questionNum > 0) {
        questionNum = lastQuestionStack[lastQuestionStack.length-1];
       //questionNum--;
        if (questionNum == 0){prevBtn.classList.add('hide');}
        if (questionNum < questions.length) {submitBtn.classList.add('hide');}
          nextQuestion(true);
    }
})

function nextQuestion(buttonPressed) {
    removeBtns();
  //  console.log("Displaying question "+questionNum);
   // console.log("question is "+questions[questionNum])
    if (buttonPressed) {
        undoMatrix();
        displayQuestion(questions[questionNum], true);
    }
    else {
      displayQuestion(questions[questionNum], false);
    }
}

submitBtn.addEventListener("click", (e) => {
    submitBtn.setAttribute("disabled", true);

    console.log(matrix)
    payload = {"matrix":matrix}
  e.preventDefault();
  $.ajax({
    type: "POST",
    contentType: 'application/json;charset=UTF-8',
    data: JSON.stringify(payload),
    url: "/ahp_data",
    success: function(response) {
        flash("Submitting questionnaire results...","success");
        setTimeout(function () {
            window.location.href = "/profile"; // redirect to profile page
         }, 1000); // runs function after 1 sec delay             
    },
    error: function(xhr, status, error) {
        flash("Error in submitting questionnaire results. Please try again.","error");
        setTimeout(function () {
            window.location.href = "/ahp"; // redirect to profile page
         }, 1000); // runs function after 1 sec delay 
    }
 });
})



function selectAnswer(e) {
  //  if (questionNum == 1) {
    if (questionNum >= questions.length) {

      submitBtn.classList.remove('hide');
      questionText.innerHTML = "Press submit to submit your answers.";
      document.getElementById("#ans-btns.btn-grid").remove();
    }    
}

function removeBtns() {
    while (answerBtns.firstChild) {
        answerBtns.removeChild(answerBtns.firstChild);
    }
    if (questionNum > 0){
        prevBtn.classList.remove('hide');
    }
}

function displayQuestion(question, undo) {
    if (!question) {
  //    console.log("heeeeeeeeeeeeeeeeee")
      return false;}
    checkTransitivity(matrix)
    questionText.innerText = question.question;
    let opt1 = question.answers[0].text;
    let opt2 = question.answers[1].text;
    if (matrix[factors.indexOf(opt1)][factors.indexOf(opt2)] != 0 && !undo) {
        questionNum = Math.min(questionNum+1, 14)
        questionNum++;
        nextQuestion(false);
        return;
    }
    question.answers.forEach(answer => {
        const btn = document.createElement("button");
        btn.innerText = answer.text;
        btn.classList.add("btn");
       
        btn.addEventListener("click", () => {
            setTimeout(function () {
                matrixStack.push(deepClone(matrix));
             }, 1); // runs function after 1 milisec delay 
             populateMatrix(opt1, opt2, btn.innerText);
             checkTransitivity(matrix)
              lastQuestionStack.push(questionNum);
            // console.log(lastQuestionStack);
            // questionNum = Math.min(questionNum+1, 14)
             questionNum++;
            
             nextQuestion(false);
        });

        btn.addEventListener("click", selectAnswer);
        answerBtns.appendChild(btn);
    });
}

function deepClone(obj) {
    if (Array.isArray(obj)) {
      return obj.map(deepClone);
    } else if (typeof obj === 'object' && obj !== null) {
      return Object.fromEntries(
        Object.entries(obj).map(([key, value]) => [key, deepClone(value)])
      );
    } else {
      return obj;
    }
  }

function populateMatrix(ans1, ans2, chosenAns) {
    let chosenIndex, otherIndex;
    if (chosenAns == "Both Equally") {
        indx1 = factors.indexOf(ans1);
        indx2 = factors.indexOf(ans2);
        matrix[indx1][indx2] = same;
        matrix[indx2][indx1] = same; 
        return ;
    }
    else if (chosenAns == ans1) {
        chosenIndex = factors.indexOf(ans1);
        otherIndex = factors.indexOf(ans2);
    }
    else {
        chosenIndex = factors.indexOf(ans2);
        otherIndex = factors.indexOf(ans1);
    }
    matrix[otherIndex][chosenIndex] = more;
    matrix[chosenIndex][otherIndex] = less;

}

function checkTransitivity(matrix) {
    // Create an empty directed graph
    let graph = {};
    for (let i = 0; i < matrix.length; i++) {
        graph[i] = new Set();
    }
    
    // Convert pairwise comparison matrix to directed graph
    for (let i = 0; i < matrix.length; i++) {
        for (let j = 0; j < matrix.length; j++) {
            if (matrix[i][j] === 3) {
                graph[j].add(i);
                matrix[i][j] = 3;
                matrix[j][i] = 1/3;
            } else if (matrix[i][j] === 1/3) {
                graph[i].add(j);
                matrix[i][j] = 1/3;
                matrix[j][i] = 3;
            } else if (matrix[i][j] === 1) {
                graph[i].add(j);
                graph[j].add(i);
                matrix[i][j] = 1;
                matrix[j][i] = 1;
            }
        }
    }
    
    // Autofill the matrix
    for (let i = 0; i < matrix.length; i++) {
        for (let j = 0; j < matrix.length; j++) {
            if (i !== j && matrix[i][j] === 0) {
                let path_exists = false;
                for (let k = 0; k < matrix.length; k++) {
                    if (k !== i && k !== j) {
                        if (matrix[i][k] === 3 && graph[j].has(k)) {
                            graph[i].add(j);
                            matrix[i][j] = 3;
                            matrix[j][i] = 1/3;
                            path_exists = true;
                            break;
                        } else if (matrix[k][j] === 3 && graph[i].has(k)) {
                            graph[j].add(i);
                            matrix[j][i] = 3;
                            matrix[i][j] = 1/3;
                            path_exists = true;
                            break;
                        } else if (matrix[i][k] === 1 && graph[j].has(k) && matrix[k][j] === 1) {
                            graph[i].add(j);
                            matrix[i][j] = 1;
                            matrix[j][i] = 1;
                            path_exists = true;
                            break;
                        } else if (matrix[k][j] === 1 && graph[i].has(k) && matrix[i][k] === 1) {
                            graph[j].add(i);
                            matrix[j][i] = 1;
                            matrix[i][j] = 1;
                            path_exists = true;
                            break;
                        }
                    }
                }
            }
        }
    }
    
    return matrix;
}
 
  function undoMatrix() {
    let num = lastQuestionStack.pop(questionNum);
  //  console.log("After popping: "+lastQuestionStack);
    let question = questions[num];
    indx1 = factors.indexOf(question.answers[0].text);
    indx2 = factors.indexOf(question.answers[1].text);
    matrix = matrixStack.pop();
  }
