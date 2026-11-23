import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.TypeLiteral;
import org.evomaster.core.EMConfig;
import org.evomaster.core.Main;
import org.evomaster.core.problem.rest.data.RestIndividual;
import org.evomaster.core.problem.rest.service.RestSecurityBuilder;
import org.evomaster.core.search.algorithms.SmartsAlgorithm;
import org.evomaster.core.search.service.SearchAlgorithm;
import org.evomaster.core.search.service.time.ExecutionPhaseController;
import java.lang.reflect.Field;
import java.util.*;

public class Wiring {
    static Object get(Object o, Class<?> owner, String name) throws Exception {
        Field f = owner.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(o);
    }
    public static void main(String[] args) throws Exception {
        String thesis = "/Users/minhnguyen/IdeaProjects/graduational-thesis";
        String[] a = {"--blackBox", "true",
            "--bbSwaggerUrl", "http://localhost:8080/v3/api-docs", "--bbTargetUrl", "http://localhost:8080",
            "--configPath", thesis + "/infra/em-config/reports-auth.yaml",
            "--useExperimentalOracles", "true", "--extraPhaseBudgetPercentage", "0.6",
            "--outputFormat", "PYTHON_UNITTEST", "--ratePerMinute", "120", "--maxTime", "150s", "--seed", "5",
            "--outputFolder", args[0]};

        EMConfig fresh = new EMConfig();
        System.out.println("DEFAULTS problemType=" + fresh.getProblemType() + " algorithm=" + fresh.getAlgorithm() + " outputFormat=" + fresh.getOutputFormat()
            + " maxTime=" + fresh.getMaxTime() + " extraPhaseBudgetPercentage=" + fresh.getExtraPhaseBudgetPercentage() + " seed=" + fresh.getSeed()
            + " ratePerMinute=" + fresh.getRatePerMinute() + " security=" + fresh.getSecurity() + " minimize=" + fresh.getMinimize()
            + " httpOracles=" + fresh.getHttpOracles() + " handleFlakiness=" + fresh.getHandleFlakiness() + " useExperimentalOracles=" + fresh.getUseExperimentalOracles()
            + " stoppingCriterion=" + fresh.getStoppingCriterion());

        Injector inj = Main.init(a);
        EMConfig c = inj.getInstance(EMConfig.class);
        System.out.println("AFTER problemType=" + c.getProblemType() + " algorithm=" + c.getAlgorithm() + " outputFormat=" + c.getOutputFormat()
            + " maxTime=" + c.getMaxTime() + " timeLimitInSeconds()=" + c.timeLimitInSeconds() + " extraPhaseBudgetPercentage=" + c.getExtraPhaseBudgetPercentage()
            + " seed=" + c.getSeed() + " ratePerMinute=" + c.getRatePerMinute() + " security=" + c.getSecurity() + " minimize=" + c.getMinimize()
            + " httpOracles=" + c.getHttpOracles() + " handleFlakiness=" + c.getHandleFlakiness() + " useExperimentalOracles=" + c.getUseExperimentalOracles()
            + " stoppingCriterion=" + c.getStoppingCriterion() + " blackBox=" + c.getBlackBox());
        System.out.println("phase budget seconds = " + (long) (c.timeLimitInSeconds() * c.getExtraPhaseBudgetPercentage()));
        System.out.println("same EMConfig twice? " + (c == inj.getInstance(EMConfig.class)));

        SearchAlgorithm<RestIndividual> alg = inj.getInstance(Key.get(new TypeLiteral<SmartsAlgorithm<RestIndividual>>() {}));
        System.out.println("algorithm object = " + alg.getClass().getSimpleName() + " getType()=" + alg.getType());
        for (String n : List.of("sampler", "ff", "archive", "randomness", "time", "config", "epc")) {
            Object v = get(alg, SearchAlgorithm.class, n);
            System.out.println("  SearchAlgorithm." + n + " -> " + v.getClass().getSimpleName() + (n.equals("config") ? " sameAsInjectorConfig=" + (v == c) : ""));
        }
        RestSecurityBuilder rsb = inj.getInstance(RestSecurityBuilder.class);
        for (String n : List.of("archive", "sampler", "fitness", "randomness", "config", "epc")) {
            Object v = get(rsb, RestSecurityBuilder.class, n);
            Object same = null;
            if (n.equals("archive")) same = get(alg, SearchAlgorithm.class, "archive");
            if (n.equals("fitness")) same = get(alg, SearchAlgorithm.class, "ff");
            if (n.equals("randomness")) same = get(alg, SearchAlgorithm.class, "randomness");
            if (n.equals("epc")) same = get(alg, SearchAlgorithm.class, "epc");
            System.out.println("  RestSecurityBuilder." + n + " -> " + v.getClass().getSimpleName() + (same != null ? " sameObjectAsInAlgorithm=" + (v == same) : ""));
        }
        Object defs = get(rsb, RestSecurityBuilder.class, "actionDefinitions");
        System.out.println("  RestSecurityBuilder.actionDefinitions size=" + ((List<?>) defs).size());
        ExecutionPhaseController epc = inj.getInstance(ExecutionPhaseController.class);
        System.out.println("epc phase before run = " + epc.getCurrentPhase());
        System.out.println("Phase timeBoxed: " + Arrays.stream(ExecutionPhaseController.Phase.values()).map(p -> p + "=" + p.getTimeBoxed()).toList());
        System.exit(0);
    }
}
