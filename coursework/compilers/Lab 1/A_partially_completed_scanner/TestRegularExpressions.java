public class TestRegularExpressions {
    public static void main(String[] args) {
        RegularExpressions re = new RegularExpressions();

        String[] ids = {"abc", "a1b2", "1abc", "_name", "A"};
        String[] nums = {"123", "0", "12a", "", "007"};
        String[] reserved = {"int", "if", "binary", "Binary"};
        String[] syms = {"(", "==", "&&", "?", ";"};
        String[] strs = {"\"hello\"", "\"\"", "noquotes", "\"unterminated"};
        String[] metas = {"// comment", "/* block */", "#directive", "normal"};

        System.out.println("--- Identifier tests ---");
        for (String s : ids) System.out.printf("%s -> %b\n", s, re.isIdentifier(s));

        System.out.println("--- Number tests ---");
        for (String s : nums) System.out.printf("%s -> %b\n", s, re.isNumber(s));

        System.out.println("--- Reserved word tests ---");
        for (String s : reserved) System.out.printf("%s -> %b\n", s, re.isReservedWord(s));

        System.out.println("--- Symbol tests ---");
        for (String s : syms) System.out.printf("%s -> %b\n", s, re.isSymbol(s));

        System.out.println("--- String tests ---");
        for (String s : strs) System.out.printf("%s -> %b\n", s, re.isString(s));

        System.out.println("--- Meta statement tests ---");
        for (String s : metas) System.out.printf("%s -> %b\n", s, re.isMetaStatement(s));
    }
}
