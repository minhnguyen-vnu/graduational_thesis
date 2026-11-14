import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.evomaster.core.problem.rest.service.RestSecurityBuilder;

public class TokensNoRegex {

    static final Pattern PART = Pattern.compile("[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+");
    static final Pattern WRONG = Pattern.compile("[A-Z]+|[a-z0-9]+");
    static final String ALPHABET = "ABCXYZabcxyz0189_-./{}[] :é中É";
    static final List<String> EDGE = Arrays.asList("", "A", "a", "1", "AB", "Ab", "aB", "A1b", "ABc", "ABC123",
            "ABC123def", "APIKey", "userRoleId", "v2Users", "V2Users", "User2FA", "user_id", "/users/{userId}/role",
            "HTTPServer", "getHTTPResponseCode", "é", "Éabc", "aÉb", "中文role", "role中文", "{id}", "--", "a-b_c.d",
            "XMLHttpRequest", "ID", "Id", "iD", "is_admin", "isAdmin", "IS_ADMIN", "ADMIN_USER", "A_b", "Z9z", "zZ9",
            "99Bottles", "ab12CD34ef");

    static boolean digitsOnly(String s) {
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < '0' || c > '9') {
                return false;
            }
        }
        return true;
    }

    static Set<String> reference(Pattern p, String text, int minLength) {
        Set<String> out = new LinkedHashSet<>();
        Matcher m = p.matcher(text);
        while (m.find()) {
            String token = m.group().toLowerCase(Locale.ROOT);
            if (token.length() < minLength || digitsOnly(token)) {
                continue;
            }
            out.add(token);
        }
        return out;
    }

    static List<String> randomStrings(int n) {
        Random rnd = new Random(20261113L);
        List<String> out = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            int len = rnd.nextInt(12);
            StringBuilder b = new StringBuilder();
            for (int j = 0; j < len; j++) {
                b.append(ALPHABET.charAt(rnd.nextInt(ALPHABET.length())));
            }
            out.add(b.toString());
        }
        return out;
    }

    public static void main(String[] args) throws Exception {
        Pattern ref = args[1].equals("wrong") ? WRONG : PART;
        List<List<String>> groups = Arrays.asList(Files.readAllLines(Paths.get(args[0])), EDGE, randomStrings(300000));
        List<String> names = Arrays.asList("corpus", "edge", "random");
        long compared = 0;
        long mismatches = 0;
        for (int g = 0; g < groups.size(); g++) {
            long bad = 0;
            String first = "";
            for (String s : groups.get(g)) {
                for (int min : new int[]{1, 4}) {
                    compared++;
                    Set<String> got = RestSecurityBuilder.Companion.tokens(s, min);
                    Set<String> want = reference(ref, s, min);
                    if (!got.equals(want)) {
                        bad++;
                        if (first.isEmpty()) {
                            first = "'" + s + "' min=" + min + " jar=" + got + " reference=" + want;
                        }
                    }
                }
            }
            mismatches += bad;
            System.out.println("GROUP " + names.get(g) + " strings=" + groups.get(g).size() + " mismatches=" + bad
                    + (first.isEmpty() ? "" : " first=" + first));
        }
        System.out.println("TOTAL compared=" + compared + " mismatches=" + mismatches);
    }
}
