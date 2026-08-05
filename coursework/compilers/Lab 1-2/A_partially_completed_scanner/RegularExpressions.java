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
		return c >= '0' && c <= '9';
		// TODO: Implement the recognition of digits 
	}
	
	/**
	 * Checks to see if the given input matches the pattern for an identifier.
	 * The pattern is: Letter(Letter|digit)*
	 * @param str The input string that is being pasrsed which will be read one charecter at a time
	 * @return boolean indicating if it is an identifier
	 */
	public boolean isIdentifier(String str) {
		if (str == null || str.length() == 0) return false;
    	// first character must be a letter
    	if (!Character.isLetter(str.charAt(0))) return false;
    	// remaining characters must be letters or digits
   		for (int i = 1; i < str.length(); i++) {
        	char c = str.charAt(i);
        	if (!Character.isLetter(c) && !isDigit(c)) return false;
    	}
    	return true;
		// TODO: Implement the recognition of identifiers 
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
		// TODO: Implement the recognition of numbers 
	}
	
	/***
	 * Checks to see if the given input matches the pattern for a reserved word.
	 * reserved words are: int, void, if, while, return, read, write, print, continue, break, binary, decimal
	 * @param str The input string that is being parsed and compaired against the list of reserved words 
	 * @return boolean indicating if it is a reserved word
	 */
	public boolean isReservedWord(String str) {
    if (str == null) return false;
    for (String w : reservedWords) {
        if (w.equals(str)) return true;
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
    for (String s : symbols) {
        if (s.equals(str)) return true;
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
    if (str == null || str.length() < 2) return false;
    if (str.charAt(0) != '"' || str.charAt(str.length() - 1) != '"') return false;
    // ensure closing quote is not escaped
    int bs = 0;
    int j = str.length() - 2;
    while (j >= 0 && str.charAt(j) == '\\') { bs++; j--; }
    if (bs % 2 == 1) return false; // closing quote is escaped -> unterminated string

    // ensure there are no unescaped internal quotes
    for (int i = 1; i < str.length() - 1; i++) {
        if (str.charAt(i) == '"') {
            int backslashes = 0;
            int k = i - 1;
            while (k >= 0 && str.charAt(k) == '\\') { backslashes++; k--; }
            if (backslashes % 2 == 0) return false; // unescaped internal quote
        }
    }
    return true;
	}
	
	/**
	 * Checks to see if the given input matches the pattern for a meta statement
	 * @param str The input string that is being parsed
	 * @return boolean indicating if it is a meta statement
	 */
	public boolean isMetaStatement(String str) {
    // Adjust the allowed leading meta characters to match your language.
    if (str == null || str.length() < 2) return false;
    char start = str.charAt(0);
    if (start != '#' && start != '@' && start != '.' && start != '%') return false;
    // require an identifier after the leading meta character
    if (!Character.isLetter(str.charAt(1))) return false;
    for (int i = 2; i < str.length(); i++) {
        char c = str.charAt(i);
        if (!Character.isLetterOrDigit(c) && c != '_') return false;
    }
    return true;
	}

}
