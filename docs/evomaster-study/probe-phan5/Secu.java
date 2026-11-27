import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.TypeLiteral;
import org.evomaster.core.Main;
import org.evomaster.core.problem.rest.data.RestCallAction;
import org.evomaster.core.problem.rest.data.RestCallResult;
import org.evomaster.core.problem.rest.data.RestIndividual;
import org.evomaster.core.problem.rest.param.BodyParam;
import org.evomaster.core.problem.rest.service.RestSecurityBuilder;
import org.evomaster.core.problem.rest.service.sampler.AbstractRestSampler;
import org.evomaster.core.search.EvaluatedIndividual;
import org.evomaster.core.search.action.ActionComponent;
import org.evomaster.core.search.algorithms.SmartsAlgorithm;
import org.evomaster.core.search.gene.utils.GeneUtils;
import org.evomaster.core.search.service.*;
import org.evomaster.core.search.service.time.ExecutionPhaseController;
import org.evomaster.core.search.service.time.SearchTimeController;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.*;
import java.util.stream.Collectors;

@SuppressWarnings({"unchecked", "rawtypes"})
public class Secu {

    static final String PROXY = "http://localhost:18080";

    static Object get(Object o, Class<?> owner, String name) throws Exception {
        Field f = owner.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(o);
    }

    static void mark(String label) throws Exception {
        HttpClient.newHttpClient().send(HttpRequest.newBuilder(URI.create(PROXY + "/__mark/" + label)).GET().build(),
            HttpResponse.BodyHandlers.discarding());
        System.out.println("=== MARK " + label);
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

    static void dumpSolution(String title, Archive<RestIndividual> archive) {
        List<EvaluatedIndividual<RestIndividual>> sol = new ArrayList<>(archive.extractSolution().getIndividuals());
        sol.sort(Comparator.comparingInt(EvaluatedIndividual::getIndex));
        System.out.println("=== " + title + " size=" + sol.size());
        for (EvaluatedIndividual<RestIndividual> ei : sol) {
            System.out.println(String.format("  idx=%d %-24s n=%d | %s", ei.getIndex(), ei.getIndividual().getSampleType(),
                ei.getIndividual().seeMainExecutableActions().size(), calls(ei, true)));
        }
    }

    static Map<String, Map<String, Double>> loadModel() throws Exception {
        Map<String, Map<String, Double>> m = new LinkedHashMap<>();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(RestSecurityBuilder.class.getResourceAsStream("/stateful-authz-model.csv")))) {
            String line;
            while ((line = r.readLine()) != null) {
                String[] row = line.trim().split(",");
                if (row.length != 3) continue;
                try {
                    m.computeIfAbsent(row[0], k -> new LinkedHashMap<>()).put(row[1], Double.parseDouble(row[2]));
                } catch (NumberFormatException e) {
                }
            }
        }
        return m;
    }

    static String weights(Map<String, Double> table, Set<String> features) {
        return features.stream().map(f -> f + "=" + (table.containsKey(f) ? String.format("%.4f", table.get(f)) : "0"))
            .collect(Collectors.joining(" "));
    }

    static void dumpModel(Injector inj) throws Exception {
        Map<String, Map<String, Double>> model = loadModel();
        System.out.println("=== MODEL tables " + model.keySet().stream().map(k -> k + ":" + model.get(k).size()).collect(Collectors.joining(" ")));
        for (String t : List.of("op", "role", "victim")) {
            System.out.println("  prior " + t + " = " + model.get(t).get("__prior__"));
        }
        AbstractRestSampler sampler = inj.getInstance(AbstractRestSampler.class);
        RestSecurityBuilder.Companion c = RestSecurityBuilder.Companion;
        for (Object o : sampler.getActionDefinitions()) {
            RestCallAction a = (RestCallAction) o;
            Set<String> fs = c.opFeatures(a);
            System.out.println(String.format("  OP %-32s score=%.4f transition=%s | %s", a.getName(), c.transitionScore(a),
                c.looksLikePermissionReducingTransition(a), weights(model.get("op"), fs)));
            for (RestSecurityBuilder.Companion.SchemaField f : c.schemaFields(a)) {
                System.out.println(String.format("      FIELD %-22s kind=%-6s enum=%s role=%.4f victim=%.4f | role: %s | victim: %s",
                    f.getKey(), f.getKind(), f.getEnumValues(), c.fieldScore("role", f), c.fieldScore("victim", f),
                    weights(model.get("role"), f.features()), weights(model.get("victim"), f.features())));
            }
        }
        for (String v : List.of("ADMIN", "VIEWER", "EVOMASTER")) {
            double low = c.valueScore("low", v), high = c.valueScore("high", v);
            System.out.println(String.format("  VALUE %-10s low=%.4f high=%.4f low-high=%.4f", v, low, high, low - high));
        }
        System.out.println("  low table: " + model.get("low"));
        System.out.println("  high table: " + model.get("high"));
    }

    public static void main(String[] args) throws Exception {
        String thesis = "/Users/minhnguyen/IdeaProjects/graduational-thesis";
        String[] a = {"--blackBox", "true",
            "--bbSwaggerUrl", PROXY + "/v3/api-docs", "--bbTargetUrl", PROXY,
            "--configPath", thesis + "/infra/em-config/reports-auth.yaml",
            "--useExperimentalOracles", "true", "--extraPhaseBudgetPercentage", "0.6",
            "--outputFormat", "PYTHON_UNITTEST", "--ratePerMinute", "120", "--maxTime", "150s", "--seed", "5",
            "--outputFolder", args[0]};
        int steps = Integer.parseInt(args[1]);

        ((ch.qos.logback.classic.Logger) org.slf4j.LoggerFactory.getLogger(RestSecurityBuilder.class))
            .setLevel(ch.qos.logback.classic.Level.DEBUG);

        Injector inj = Main.init(a);
        SmartsAlgorithm<RestIndividual> alg = inj.getInstance(Key.get(new TypeLiteral<SmartsAlgorithm<RestIndividual>>() {}));
        Sampler<RestIndividual> sampler = (Sampler<RestIndividual>) get(alg, SearchAlgorithm.class, "sampler");
        FitnessFunction<RestIndividual> ff = (FitnessFunction<RestIndividual>) get(alg, SearchAlgorithm.class, "ff");
        Archive<RestIndividual> archive = (Archive<RestIndividual>) get(alg, SearchAlgorithm.class, "archive");
        SearchTimeController time = inj.getInstance(SearchTimeController.class);
        ExecutionPhaseController epc = inj.getInstance(ExecutionPhaseController.class);

        mark("SEARCH");
        epc.markStartingSearch();
        time.startSearch();
        long t0 = System.currentTimeMillis();
        for (int k = 1; k <= steps; k++) {
            RestIndividual ind = sampler.sample(false);
            String type = ind.getSampleType().toString();
            EvaluatedIndividual<RestIndividual> ei = ff.calculateCoverage(ind, Set.of(), null);
            boolean added = ei != null && archive.addIfNeeded(ei);
            long users = ind.seeMainExecutableActions().stream().map(x -> x.getAuth().getName()).distinct().count();
            System.out.println(String.format("#%03d t=%5.1fs %-26s n=%d users=%d | %s | added=%s covered=%d reached=%d",
                k, (System.currentTimeMillis() - t0) / 1000.0, type, ind.seeMainExecutableActions().size(), users,
                ei == null ? "EVAL FAILED" : calls(ei, false), added, archive.numberOfCoveredTargets(), archive.numberOfReachedTargets()));
        }
        Method after = SearchAlgorithm.class.getDeclaredMethod("handleAfterSearch");
        after.setAccessible(true);
        after.invoke(alg);
        System.out.println("=== SEARCH END evaluatedIndividuals=" + time.getEvaluatedIndividuals() + " evaluatedActions=" + time.getEvaluatedActions()
            + " covered=" + archive.numberOfCoveredTargets() + " solution=" + archive.extractSolution().getIndividuals().size());

        mark("MINIMIZATION");
        epc.markStartingMinimization();
        Minimizer<RestIndividual> minimizer = (Minimizer<RestIndividual>) inj.getInstance(Key.get(new TypeLiteral<Minimizer<RestIndividual>>() {}));
        minimizer.applyPhase();
        dumpSolution("SOLUTION BEFORE SECURITY", archive);
        dumpModel(inj);

        mark("SECURITY");
        epc.markStartingSecurity();
        RestSecurityBuilder builder = inj.getInstance(RestSecurityBuilder.class);
        builder.applySecurityPhase();
        mark("END");

        for (String f : List.of("privilegeReducedInPhase", "privilegeReducedByProof", "skippedTransitionVictims",
            "statefulTripleAttempts", "privilegeRestoreAttempts", "candidateAttempts", "candidateProven")) {
            System.out.println("  builder." + f + " = " + get(builder, RestSecurityBuilder.class, f));
        }
        dumpSolution("SOLUTION AFTER SECURITY", archive);
        IdMapper idMapper = inj.getInstance(IdMapper.class);
        for (EvaluatedIndividual<RestIndividual> ei : archive.extractSolution().getIndividuals()) {
            for (Integer id : ei.getFitness().getViewOfData().keySet()) {
                String desc = idMapper.getDescriptiveId(id);
                if (desc != null && desc.contains("970")) {
                    System.out.println("  FAULT target id=" + id + " desc=" + desc + " score=" + ei.getFitness().getViewOfData().get(id).getScore()
                        + " test idx=" + ei.getIndex() + " | " + calls(ei, true));
                }
            }
            for (Object r : ei.seeResults(null)) {
                if (r instanceof RestCallResult rr && !rr.getFaults().isEmpty()) {
                    System.out.println("  DetectedFault on action " + rr.getSourceLocalId() + " status=" + rr.getStatusCode() + " " + rr.getFaults());
                }
            }
        }
        System.exit(0);
    }
}
