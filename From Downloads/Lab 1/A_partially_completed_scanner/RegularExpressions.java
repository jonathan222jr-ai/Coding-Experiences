/**
 * This class implements the regular expressions used to parse the input
 */

public class RegularExpressions {
	
	
	// Array of reserved words
	private String [] reservedWords = {"int","void","if","while","return","read","write","print","continue","break","binary",
			"decimal"};
	
	// Array of symbols
	private String [] symbols = {"(",")","{","}","[","]",",",";","+","-","*","/","==","!=",">",">=","<","<=",
			"=","&&","||"};
	
	/**
	 * Checks to see if the input matches a space. A space is defined as tab, spacebar, newline
	 * @param str The String to be checked
	 * @return boolean indicating if it is a space
	 */
	public boolean isSpace(String str) {
		char ch;
		for (int i = 0; i < str.length(); i++) {
			ch = str.charAt(i);
			if(ch != ' ' && ch != '\n' && ch != '\r' && ch != '\u001a' && ch != '\t') {
				// this is not space
				return false;
			}
		}
		return true;
	}
	
	/***
	 * Checks to see if a character is a digit
	 * @param c the character to check 
	 * @return boolean indicating if it is a digit
	 */
	private boolean isDigit(char c) {
		// A digit is any character between '0' and '9'
		return (c >= '0' && c <= '9');
	}
	
	/**
	 * Checks to see if the given input matches the pattern for an identifier.
	 * The pattern is: Letter(Letter|digit)*
	 * @param str The input string that is being pasrsed which will be read one charecter at a time
	 * @return boolean indicating if it is an identifier
	 */
	public boolean isIdentifier(String str) {		
		if (str == null || str.length() == 0) return false;
		// First character must be a letter
		char ch = str.charAt(0);
		if (!Character.isLetter(ch)) return false;
		// Remaining characters may be letters or digits
		for (int i = 1; i < str.length(); i++) {
			ch = str.charAt(i);
			if (!Character.isLetter(ch) && !isDigit(ch)) {
				return false;
			}
		}
		return true;
	}

	/***
	 * Checks to see if the given input matches the pattern for a number.
	 * The pattern for number is: digit+
	 * @param str The input string that is being parsed which will be read one character at a time
	 * @return boolean indicating if it is a number
	 */
	public boolean isNumber(String str) {
		if (str == null || str.length() == 0) return false;
		for (int i = 0; i < str.length(); i++) {
			if (!isDigit(str.charAt(i))) return false;
		}
		return true;
	}
	
	/***
	 * Checks to see if the given input matches the pattern for a reserved word.
	 * reserved words are: int, void, if, while, return, read, write, print, continue, break, binary, decimal
	 * @param str The input string that is being parsed and compaired against the list of reserved words 
	 * @return boolean indicating if it is a reserved word
	 */
	public boolean isReservedWord(String str) {
		if (str == null) return false;
		for (int i = 0; i < reservedWords.length; i++) {
			if (reservedWords[i].equals(str)) return true;
		}
		return false;
	}
	
	/***
	 * Checks to see if the given input matches the pattern for a symbol
	 * @param str The input string that is being parsed and compaired against the list of symbols
	 * @return boolean indicating if it is a symbol
	 */
	public boolean isSymbol(String str) {
		if (str == null) return false;
		for (int i = 0; i < symbols.length; i++) {
			if (symbols[i].equals(str)) return true;
		}
		return false;
	}
	
	/**
	 * Checks to see if the given input matches the pattern for a string
	 * The pattern for a string is that it starts and ends with quotations 
	 * @param str The input string that is being parsed
	 * @return boolean indicating if it is a string
	 */
	public boolean isString(String str) {
		if (str == null) return false;
		// A string must start and end with a double quote and be at least 2 characters long
		if (str.length() < 2) return false;
		return (str.charAt(0) == '"' && str.charAt(str.length() - 1) == '"');
	}
	
	/**
	 * Checks to see if the given input matches the pattern for a meta statement
	 * @param str The input string that is being parsed
	 * @return boolean indicating if it is a meta statement
	 */
	public boolean isMetaStatement(String str) {
		if (str == null) return false;
		String t = str.trim();
		// Treat common comment/meta forms as meta statements: // line comments, /* block comments */, and # directives
		if (t.startsWith("//")) return true;
		if (t.startsWith("/*") && t.endsWith("*/")) return true;
		if (t.startsWith("#")) return true;
		return false;
	}

}
