// ---------------- Get Elements ----------------

// get the calculator display element (the text input that shows numbers/results)
const display = document.getElementById("display");         

// get all number buttons (0–9) by their shared class "number"
const numberButtons = document.querySelectorAll(".number"); 

// get all operator buttons (+, -, *, /) by their shared class "operator"
const operatorButtons = document.querySelectorAll(".operator"); 

// get the decimal button (.)
const decimalButton = document.querySelector(".decimal");   

// get the equals (=) button
const equalsButton = document.getElementById("equals");     

// get the clear (C) button
const clearButton = document.getElementById("clear");       

// get the expression display element (shows the equation being typed, like "5 + 5")
const expressionDisplay = document.getElementById("expression");


// ---------------- Calculator State ----------------

// stores first operand (number before operator, e.g., "5" in "5 + 2")
let firstNumber = "";          

// stores second operand (number after operator, e.g., "2" in "5 + 2")
let secondNumber = "";         

// stores chosen operator (+, -, *, /)
let currentOperator = null;    

// flag to know if display should be cleared when typing the next number
let shouldResetDisplay = false;

// stores last operation (used for repeating calculations with "=")
let lastOperation = null;      


// ---------------- Numbers ----------------
numberButtons.forEach(button => {                           
  // add click event for each number button
  button.addEventListener("click", () => {                  
    if (shouldResetDisplay) {                               // if flag is true (after operator or calculation)...
      display.value = "";                                   // clear the display
      shouldResetDisplay = false;                           // reset flag
    }
    display.value += button.textContent;                    // append the clicked number to display

    // remove highlight from operator buttons when typing a number
    operatorButtons.forEach(btn => btn.classList.remove("active")); 
    
    // highlight the pressed number button
    numberButtons.forEach(btn => btn.classList.remove("active")); 
    button.classList.add("active");
  });
});


// ---------------- Decimal ----------------
decimalButton.addEventListener("click", () => {             
  if (shouldResetDisplay) {                                // if we just calculated or pressed operator...
    display.value = "0";                                    // start with "0."
    shouldResetDisplay = false;                             // reset flag
  }
  if (!display.value.includes(".")) {                       // only allow one decimal point per number
    display.value += ".";                                   // append decimal
  }
});


// ---------------- Operators ----------------
operatorButtons.forEach(button => {                         
  // add click event for each operator button
  button.addEventListener("click", () => {                  
    if (currentOperator !== null && !shouldResetDisplay) {  // if an operator was already chosen and second number entered...
      secondNumber = display.value;                         // set second number from display
      calculate();                                          // calculate immediately (chaining)
      lastOperation = { operator: currentOperator, number: secondNumber }; // store last operation
    }
    firstNumber = display.value;                            // save current number as first operand
    currentOperator = button.textContent;                   // save clicked operator
    shouldResetDisplay = true;                              // flag: next number should reset the display
    
    // update expression display to show the current equation (e.g., "5 +")
    expressionDisplay.textContent = firstNumber + " " + currentOperator;

    // highlight the selected operator button
    operatorButtons.forEach(btn => btn.classList.remove("active")); 
    button.classList.add("active");                         
  });
});


// ---------------- Equals (=) ----------------
equalsButton.addEventListener("click", () => {              
  if (currentOperator === null && lastOperation) {          // if "=" pressed with no new operator, repeat last operation
    firstNumber = display.value;                            // current result becomes first number
    currentOperator = lastOperation.operator;               // use operator from last operation
    secondNumber = lastOperation.number;                    // use second number from last operation
    expressionDisplay.textContent = firstNumber + " " + currentOperator + " " + secondNumber + " ="; // show equation
    calculate();                                            // perform calculation
    currentOperator = null;                                 // reset operator so repeat "=" works again
  } else if (currentOperator !== null) {                    // if we have a pending operator...
    secondNumber = display.value;                           // set second number
    expressionDisplay.textContent = firstNumber + " " + currentOperator + " " + secondNumber + " ="; // show equation
    calculate();                                            // perform calculation
    lastOperation = { operator: currentOperator, number: secondNumber }; // save operation for repeat
    currentOperator = null;                                 // reset operator after calculation
    operatorButtons.forEach(btn => btn.classList.remove("active")); // remove highlight from operators
  }
});


// ---------------- Clear (C) ----------------
clearButton.addEventListener("click", clear);               // when "C" pressed, run clear function


// ---------------- Calculate Function ----------------
function calculate() {                                      
  let result;                                               
  const a = parseFloat(firstNumber);                        // convert first number string to float
  const b = parseFloat(secondNumber || display.value);      // convert second number string to float (fallback: display)

  // perform operation depending on chosen operator
  switch (currentOperator) {                                
    case "+": result = a + b; break;                        
    case "-": result = a - b; break;                        
    case "*": result = a * b; break;                        
    case "/": result = b !== 0 ? a / b : "Error"; break;    // prevent divide by 0
  }

  display.value = result;                                   // update display with result
  firstNumber = result;                                     // store result as new first number
  shouldResetDisplay = true;                                // next number press clears the display
}


// ---------------- Clear Function ----------------
function clear() {                                          
  display.value = "";                                       // clear calculator display
  expressionDisplay.textContent = "";                       // clear equation display
  firstNumber = "";                                         // reset first number
  secondNumber = "";                                        // reset second number
  currentOperator = null;                                   // reset operator
  lastOperation = null;                                     // reset last operation
  operatorButtons.forEach(btn => btn.classList.remove("active")); // remove highlights from operator buttons
}
