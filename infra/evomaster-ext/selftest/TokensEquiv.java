import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TokensEquiv {

    static final Pattern PIECE = Pattern.compile("[^A-Za-z0-9]+");
    static final Pattern PART = Pattern.compile("[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+");
    static final Pattern WRONG = Pattern.compile("[A-Z]+(?![a-z_])|[A-Z][a-z0-9]*|[a-z0-9]+");
    static final String ALPHABET = "ABCXYZabcxyz0189_-./{}[] :é中";

    static List<String> matches(Pattern p, String s) {
        List<String> out = new ArrayList<>();
        Matcher m = p.matcher(s);
        while (m.find()) {
            out.add(m.group());
        }
        return out;
    }

    static List<String> perPiece(String s) {
        List<String> out = new ArrayList<>();
        for (String piece : PIECE.split(s, -1)) {
            out.addAll(matches(PART, piece));
        }
        return out;
    }

    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        Random random = new Random(20261103L);
        int different = 0;
        int wrongDifferent = 0;
        for (int i = 0; i < n; i++) {
            int length = random.nextInt(24);
            StringBuilder sb = new StringBuilder();
            for (int j = 0; j < length; j++) {
                sb.append(ALPHABET.charAt(random.nextInt(ALPHABET.length())));
            }
            String s = sb.toString();
            List<String> expected = perPiece(s);
            if (!expected.equals(matches(PART, s))) {
                different++;
            }
            if (!expected.equals(matches(WRONG, s))) {
                wrongDifferent++;
            }
        }
        System.out.println(n + " strings, different " + different + ", boundary-control different " + wrongDifferent);
        System.exit(different == 0 && wrongDifferent > 0 ? 0 : 1);
    }
}
