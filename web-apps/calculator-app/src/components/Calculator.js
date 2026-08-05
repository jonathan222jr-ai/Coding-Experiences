import React, { useState } from "react";
import { Button, TextField, Paper, Grid, Typography } from "@mui/material";
import "./Calculator.css";

export default function Calculator() {
  const [display, setDisplay] = useState("");
  const [expression, setExpression] = useState("");
  const [firstNumber, setFirstNumber] = useState("");
  const [secondNumber, setSecondNumber] = useState("");
  const [currentOperator, setCurrentOperator] = useState(null);
  const [shouldResetDisplay, setShouldResetDisplay] = useState(false);
  const [lastOperation, setLastOperation] = useState(null);

  // ---------------- Numbers ----------------
  const handleNumberClick = (num) => {
    if (shouldResetDisplay) {
      setDisplay(num);
      setShouldResetDisplay(false);
    } else {
      setDisplay(display + num);
    }
  };

  // ---------------- Decimal ----------------
  const handleDecimalClick = () => {
    if (shouldResetDisplay) {
      setDisplay("0.");
      setShouldResetDisplay(false);
    } else if (!display.includes(".")) {
      setDisplay(display + ".");
    }
  };

  // ---------------- Operators ----------------
  const handleOperatorClick = (op) => {
    if (currentOperator !== null && !shouldResetDisplay) {
      const result = calculate(firstNumber, display, currentOperator);
      setDisplay(result);
      setFirstNumber(result);
      setLastOperation({ operator: currentOperator, number: display });
    } else {
      setFirstNumber(display);
    }
    setCurrentOperator(op);
    setShouldResetDisplay(true);
    setExpression(`${display} ${op}`);
  };

  // ---------------- Equals (=) ----------------
  const handleEquals = () => {
    if (currentOperator === null && lastOperation) {
      const result = calculate(display, lastOperation.number, lastOperation.operator);
      setExpression(`${display} ${lastOperation.operator} ${lastOperation.number} =`);
      setDisplay(result);
    } else if (currentOperator !== null) {
      const result = calculate(firstNumber, display, currentOperator);
      setExpression(`${firstNumber} ${currentOperator} ${display} =`);
      setDisplay(result);
      setLastOperation({ operator: currentOperator, number: display });
      setCurrentOperator(null);
    }
    setShouldResetDisplay(true);
  };

  // ---------------- Calculate ----------------
  const calculate = (a, b, op) => {
    const x = parseFloat(a);
    const y = parseFloat(b);
    if (isNaN(x) || isNaN(y)) return "";
    switch (op) {
      case "+": return (x + y).toString();
      case "-": return (x - y).toString();
      case "*": return (x * y).toString();
      case "/": return y !== 0 ? (x / y).toString() : "Error";
      default: return "";
    }
  };

  // ---------------- Clear ----------------
  const handleClear = () => {
    setDisplay("");
    setExpression("");
    setFirstNumber("");
    setSecondNumber("");
    setCurrentOperator(null);
    setLastOperation(null);
    setShouldResetDisplay(false);
  };

  // ---------------- Button Layout ----------------
  const buttons = [
    "7","8","9","/",
    "4","5","6","*",
    "1","2","3","-",
    "0",".","=","+"
  ];

  return (
    <Paper elevation={4} className="calculator">
      <Typography id="expression" variant="subtitle1">{expression}</Typography>
      <TextField
        id="display"
        fullWidth
        value={display}
        disabled
        variant="outlined"
        InputProps={{ style: { textAlign: "right", fontSize: "24px" } }}
      />
      <Grid container spacing={1} className="buttons">
        {buttons.map((item) => (
          <Grid item xs={3} key={item}>
            <Button
              fullWidth
              variant="contained"
              className={
                item === "="
                  ? "equals"
                  : item === "." 
                  ? "decimal"
                  : ["+","-","*","/"].includes(item)
                  ? "operator"
                  : "number"
              }
              onClick={() => {
                if (!isNaN(item)) handleNumberClick(item);
                else if (item === ".") handleDecimalClick();
                else if (item === "=") handleEquals();
                else handleOperatorClick(item);
              }}
            >
              {item}
            </Button>
          </Grid>
        ))}
        <Grid item xs={12}>
          <Button
            fullWidth
            variant="outlined"
            color="error"
            id="clear"
            onClick={handleClear}
          >
            C
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
}
