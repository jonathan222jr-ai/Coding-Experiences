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
		if(c >= '0' && c <= '9') {
			return true;
		}
		return false;
	}
	
	/**
	 * Checks to see if the given input matches the pattern for an identifier.
	 * The pattern is: Letter(Letter|digit)*
	 * @param str The input string that is being pasrsed which will be read one charecter at a time
	 * @return boolean indicating if it is an identifier
	 */
	public boolean isIdentifier(String str) {		
		if(str == null || str.length() == 0) return false;
		char first = str.charAt(0);
		if(!(Character.isLetter(first) || first == '_')) return false;
		for(int i = 1; i < str.length(); i++) {
			char c = str.charAt(i);
			if(!(Character.isLetter(c) || isDigit(c) || c == '_')) {
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
		if(str == null || str.length() == 0) return false;
		for(int i = 0; i < str.length(); i++) {
			if(!isDigit(str.charAt(i))) return false;
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
		if(str == null) return false;
		for(String w : reservedWords) {
			if(str.equals(w)) return true;
		}
		return false;
	}
	
	/***
	 * Checks to see if the given input matches the pattern for a symbol
	 * @param str The input string that is being parsed and compaired against the list of symbols
	 * @return boolean indicating if it is a symbol
	 */
	public boolean isSymbol(String str) {
		if(str == null) return false;
		for(String s : symbols) {
			if(str.equals(s)) return true;
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
		if(str == null) return false;
		if(str.length() >= 2 && str.charAt(0) == '"' && str.charAt(str.length() - 1) == '"') {
			return true;
		}
		return false;
	}
	
	/**
	 * Checks to see if the given input matches the pattern for a meta statement
	 * @param str The input string that is being parsed
	 * @return boolean indicating if it is a meta statement
	 */
	public boolean isMetaStatement(String str) {
		if(str == null || str.length() == 0) return false;
		// Lines starting with # (e.g., #include, #define) are meta statements
		if(str.startsWith("#")) return true;
		// C++ style comments are meta statements (//...)
		if(str.startsWith("//")) return true;
		return false;
	}

}
