import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.TypeLiteral;
import org.evomaster.core.Main;
import org.evomaster.core.problem.rest.data.RestCallAction;
import org.evomaster.core.problem.rest.data.RestCallResult;
import org.evomaster.core.problem.rest.data.RestIndividual;
import org.evomaster.core.problem.rest.param.BodyParam;
import org.evomaster.core.search.EvaluatedIndividual;
import org.evomaster.core.search.action.ActionComponent;
import org.evomaster.core.search.algorithms.SmartsAlgorithm;
import org.evomaster.core.search.gene.utils.GeneUtils;
import org.evomaster.core.search.service.*;
import org.evomaster.core.search.service.time.SearchTimeController;
import java.lang.reflect.Field;
import java.util.*;
import java.util.stream.Collectors;

@SuppressWarnings({"unchecked", "rawtypes"})
public class Smarts147 {

    static Object get(Object o, Class<?> owner, String name) throws Exception {
        Field f = owner.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(o);
    }

    static Integer status(EvaluatedIndividual<RestIndividual> ei, ActionComponent a) {
        Object r = ei.seeResult(a.getLocalId());
        return r == null ? null : ((RestCallResult) r).getStatusCode();
    }

    static String body(RestCallAction a) {
        for (Object p : a.getParameters()) {
            if (p instanceof BodyParam bp) {
                try {
                    return " " + bp.primaryGene().getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false);
                } catch (Throwable t) {
                    return " <" + t.getClass().getSimpleName() + ">";
                }
            }
        }
        return "";
    }

    static String calls(EvaluatedIndividual<RestIndividual> ei, boolean withBody) {
        return ei.getIndividual().seeMainExecutableActions().stream()
            .map(x -> x.getAuth().getName() + " " + x.getVerb() + " " + x.getPath() + (x.getUsePreviousLocationId() != null ? "[loc]" : (x.getPath().toString().contains("{") ? "=" + x.resolvedPath() : ""))
                + (withBody ? body(x) : "") + " ->" + status(ei, x))
            .collect(Collectors.joining(" ; "));
    }

    public static void main(String[] args) throws Exception {
        String thesis = "/Users/minhnguyen/IdeaProjects/graduational-thesis";
        String[] a = {"--blackBox", "true",
            "--bbSwaggerUrl", "http://localhost:8080/v3/api-docs", "--bbTargetUrl", "http://localhost:8080",
            "--configPath", thesis + "/infra/em-config/reports-auth.yaml",
            "--useExperimentalOracles", "true", "--extraPhaseBudgetPercentage", "0.6",
            "--outputFormat", "PYTHON_UNITTEST", "--ratePerMinute", "120", "--maxTime", "150s", "--seed", "5",
            "--outputFolder", args[0]};
        int steps = Integer.parseInt(args[1]);

        Injector inj = Main.init(a);
        SmartsAlgorithm<RestIndividual> alg = inj.getInstance(Key.get(new TypeLiteral<SmartsAlgorithm<RestIndividual>>() {}));
        Sampler<RestIndividual> sampler = (Sampler<RestIndividual>) get(alg, SearchAlgorithm.class, "sampler");
        FitnessFunction<RestIndividual> ff = (FitnessFunction<RestIndividual>) get(alg, SearchAlgorithm.class, "ff");
        Archive<RestIndividual> archive = (Archive<RestIndividual>) get(alg, SearchAlgorithm.class, "archive");
        SearchTimeController time = inj.getInstance(SearchTimeController.class);

        time.startSearch();
        long t0 = System.currentTimeMillis();
        Map<String, Integer> byType = new TreeMap<>();
        Map<Integer, Integer> bySize = new TreeMap<>();
        int multiUser = 0;
        int mainActions = 0;
        for (int k = 1; k <= steps; k++) {
            RestIndividual ind = sampler.sample(false);
            String type = ind.getSampleType().toString();
            EvaluatedIndividual<RestIndividual> ei = ff.calculateCoverage(ind, Set.of(), null);
            boolean added = ei != null && archive.addIfNeeded(ei);
            int n = ind.seeMainExecutableActions().size();
            mainActions += n;
            byType.merge(type, 1, Integer::sum);
            bySize.merge(n, 1, Integer::sum);
            long users = ind.seeMainExecutableActions().stream().map(x -> x.getAuth().getName()).distinct().count();
            if (users > 1) multiUser++;
            String cleanup = ei == null ? "" : ei.getIndividual().seeCleanUpActions().stream()
                .map(x -> ((RestCallAction) x).getVerb() + " " + ((RestCallAction) x).getPath() + "->" + status(ei, x)).collect(Collectors.joining(","));
            System.out.println(String.format("#%03d t=%5.1fs %-26s n=%d users=%d | %s | cleanup=[%s] | added=%s covered=%d reached=%d",
                k, (System.currentTimeMillis() - t0) / 1000.0, type, n, users, ei == null ? "EVAL FAILED" : calls(ei, false), cleanup, added,
                archive.numberOfCoveredTargets(), archive.numberOfReachedTargets()));
        }
        System.out.println("=== SUMMARY");
        System.out.println("elapsed=" + (System.currentTimeMillis() - t0) / 1000.0 + "s evaluatedIndividuals=" + time.getEvaluatedIndividuals() + " evaluatedActions=" + time.getEvaluatedActions() + " sumMainActions=" + mainActions);
        System.out.println("bySampleType=" + byType);
        System.out.println("bySize=" + bySize);
        System.out.println("multiUserTests=" + multiUser);
        System.out.println("archive covered=" + archive.numberOfCoveredTargets() + " reached=" + archive.numberOfReachedTargets() + " notCovered=" + archive.notCoveredTargets().size());
        List<EvaluatedIndividual<RestIndividual>> sol = archive.extractSolution().getIndividuals();
        System.out.println("solution size=" + sol.size());
        sol.sort(Comparator.comparingInt(EvaluatedIndividual::getIndex));
        for (EvaluatedIndividual<RestIndividual> ei : sol) {
            System.out.println(String.format("  step#%03d %-26s n=%d | %s", ei.getIndex() + 1, ei.getIndividual().getSampleType(), ei.getIndividual().seeMainExecutableActions().size(), calls(ei, true)));
        }
        System.exit(0);
    }
}
