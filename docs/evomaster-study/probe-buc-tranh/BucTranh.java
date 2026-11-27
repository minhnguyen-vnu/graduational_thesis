import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.TypeLiteral;
import org.evomaster.core.Main;
import org.evomaster.core.problem.rest.data.RestCallAction;
import org.evomaster.core.problem.rest.data.RestCallResult;
import org.evomaster.core.problem.rest.data.RestIndividual;
import org.evomaster.core.problem.rest.service.sampler.AbstractRestSampler;
import org.evomaster.core.search.EvaluatedIndividual;
import org.evomaster.core.search.FitnessValue;
import org.evomaster.core.search.Heuristics;
import org.evomaster.core.search.action.ActionComponent;
import org.evomaster.core.search.algorithms.SmartsAlgorithm;
import org.evomaster.core.search.service.*;
import org.evomaster.core.search.service.time.SearchTimeController;
import java.lang.reflect.Field;
import java.util.*;
import java.util.stream.Collectors;

@SuppressWarnings({"unchecked", "rawtypes"})
public class BucTranh {

    static Object get(Object o, Class<?> owner, String name) throws Exception {
        Field f = owner.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(o);
    }

    static Integer status(EvaluatedIndividual<RestIndividual> ei, ActionComponent a) {
        Object r = ei.seeResult(a.getLocalId());
        return r == null ? null : ((RestCallResult) r).getStatusCode();
    }

    static String call(RestCallAction x) {
        String p = x.getUsePreviousLocationId() != null ? x.getPath() + "[loc]"
            : (x.getPath().toString().contains("{") ? x.resolvedPath() : x.getPath().toString());
        return x.getAuth().getName() + " " + x.getVerb() + " " + p;
    }

    static String calls(EvaluatedIndividual<RestIndividual> ei) {
        return ei.getIndividual().seeMainExecutableActions().stream()
            .map(x -> call(x) + " ->" + status(ei, x)).collect(Collectors.joining(" ; "));
    }

    static String plain(RestIndividual ind) {
        return ind.seeMainExecutableActions().stream().map(BucTranh::call).collect(Collectors.joining(" ; "));
    }

    static void dumpFv(String title, EvaluatedIndividual<RestIndividual> ei, IdMapper m) {
        FitnessValue fv = ei.getFitness();
        System.out.println("  " + title + " step#" + (ei.getIndex() + 1) + " | " + calls(ei) + " | size=" + fv.getSize());
        List<Map.Entry<Integer, Heuristics>> es = new ArrayList<>(fv.getViewOfData().entrySet());
        es.sort(Map.Entry.comparingByKey(Comparator.reverseOrder()));
        for (Map.Entry<Integer, Heuristics> e : es) {
            System.out.println("    targets[" + e.getKey() + "] score=" + e.getValue().getScore()
                + " actionIndex=" + e.getValue().getActionIndex() + " \"" + m.getDescriptiveId(e.getKey()) + "\"");
        }
    }

    public static void main(String[] args) throws Exception {
        String thesis = "/Users/minhnguyen/IdeaProjects/graduational-thesis";
        String seed = args[1];
        int steps = Integer.parseInt(args[2]);
        String[] a = {"--blackBox", "true",
            "--bbSwaggerUrl", "http://localhost:8080/v3/api-docs", "--bbTargetUrl", "http://localhost:8080",
            "--configPath", thesis + "/infra/em-config/reports-auth.yaml",
            "--useExperimentalOracles", "true", "--extraPhaseBudgetPercentage", "0.6",
            "--outputFormat", "PYTHON_UNITTEST", "--ratePerMinute", "120", "--maxTime", "150s", "--seed", seed,
            "--outputFolder", args[0]};

        Injector inj = Main.init(a);
        SmartsAlgorithm<RestIndividual> alg = inj.getInstance(Key.get(new TypeLiteral<SmartsAlgorithm<RestIndividual>>() {}));
        AbstractRestSampler sampler = (AbstractRestSampler) get(alg, SearchAlgorithm.class, "sampler");
        FitnessFunction<RestIndividual> ff = (FitnessFunction<RestIndividual>) get(alg, SearchAlgorithm.class, "ff");
        Archive<RestIndividual> archive = (Archive<RestIndividual>) get(alg, SearchAlgorithm.class, "archive");
        IdMapper idMapper = inj.getInstance(IdMapper.class);
        SearchTimeController time = inj.getInstance(SearchTimeController.class);
        Map<Integer, List<EvaluatedIndividual<RestIndividual>>> pops = (Map) get(archive, Archive.class, "populations");
        Map<Integer, String> mapping = (Map) get(idMapper, IdMapper.class, "mapping");

        System.out.println("=== CONFIG probOfSmartSampling=" + inj.getInstance(org.evomaster.core.EMConfig.class).getProbOfSmartSampling()
            + " maxTestSize=" + sampler.getMaxTestSizeDuringSampler() + " seed=" + seed);
        System.out.println("same IdMapper in ff/archive: " + (get(ff, FitnessFunction.class, "idMapper") == idMapper) + "/" + (get(archive, Archive.class, "idMapper") == idMapper));
        System.out.println("=== ADHOC after customizeAdHocInitialIndividuals");
        List<RestIndividual> adHoc = sampler.getNotExecutedAdHocInitialIndividuals();
        System.out.println("size=" + adHoc.size() + " hasSpecialInitForSmartSampler=" + sampler.hasSpecialInitForSmartSampler()
            + " idMapper.mapping.size=" + mapping.size());
        for (int i = 0; i < adHoc.size(); i++) {
            System.out.println("  [" + i + "] " + adHoc.get(i).getSampleType() + " " + plain(adHoc.get(i)));
        }

        System.out.println("=== LOOP sample -> calculateCoverage -> addIfNeeded");
        time.startSearch();
        long t0 = System.currentTimeMillis();
        int mainActions = 0;
        Map<String, Integer> byBranch = new TreeMap<>();
        Map<Integer, Integer> firstStep = new HashMap<>();
        for (int k = 1; k <= steps; k++) {
            int pre = sampler.getSizeOfAdHocInitialIndividuals();
            boolean special = sampler.hasSpecialInitForSmartSampler();
            Set<Integer> before = new HashSet<>(pops.keySet());
            RestIndividual ind = sampler.sample(false);
            int post = sampler.getSizeOfAdHocInitialIndividuals();
            String type = ind.getSampleType().toString();
            List<RestCallAction> acts = ind.seeMainExecutableActions();
            String branch;
            if (pre > 0) {
                branch = "adHoc[" + (pre - 1) + "]";
            } else if (type.equals("RANDOM")) {
                branch = "random";
            } else {
                RestCallAction chosen = null;
                for (RestCallAction x : acts) if (x.getBackwardLinkReference() == null) chosen = x;
                branch = "smart:" + (chosen == null ? "?" : chosen.getVerb());
            }
            EvaluatedIndividual<RestIndividual> ei = ff.calculateCoverage(ind, Set.of(), null);
            boolean added = ei != null && archive.addIfNeeded(ei);
            mainActions += acts.size();
            byBranch.merge(branch.startsWith("adHoc") ? "adHoc" : branch, 1, Integer::sum);
            List<Integer> fresh = pops.keySet().stream().filter(t -> !before.contains(t)).sorted(Comparator.reverseOrder()).toList();
            for (Integer t : fresh) firstStep.put(t, k);
            System.out.println(String.format("#%03d t=%5.1fs special=%s adHoc %d->%d %-12s %-26s | %s | fv=%d | added=%s covered=%d reached=%d | new=%s",
                k, (System.currentTimeMillis() - t0) / 1000.0, special, pre, post, branch, type,
                ei == null ? "EVAL FAILED" : calls(ei), ei == null ? 0 : ei.getFitness().getViewOfData().size(), added,
                archive.numberOfCoveredTargets(), archive.numberOfReachedTargets(),
                fresh.stream().map(t -> t + "=" + idMapper.getDescriptiveId(t)).toList()));
            if (k == 1 && ei != null) dumpFv("FV of first test", ei, idMapper);
        }

        System.out.println("=== SUMMARY");
        System.out.println("elapsed=" + (System.currentTimeMillis() - t0) / 1000.0 + "s evaluatedIndividuals=" + time.getEvaluatedIndividuals()
            + " evaluatedActions=" + time.getEvaluatedActions() + " sumMainActions=" + mainActions);
        System.out.println("byBranch=" + byBranch);
        System.out.println("archive covered=" + archive.numberOfCoveredTargets() + " reached=" + archive.numberOfReachedTargets()
            + " populations.size=" + pops.size());
        System.out.println("idMapper.mapping.size=" + mapping.size() + " localCounter=" + get(idMapper, IdMapper.class, "localCounter"));
        System.out.println("extractSolution().individuals.size=" + archive.extractSolution().getIndividuals().size());

        System.out.println("=== KEY TARGETS");
        List<String> keys = List.of("Auth:alice:PUT:/reports/{id}:2xx", "200:PUT:/reports/{id}", "403:PUT:/reports/{id}",
            "Auth:bob:PUT:/reports/{id}:403", "Auth:superadmin:PUT:/users/{username}/role:2xx", "200:PUT:/users/{username}/role",
            "HTTP_FAULT:PUT:/reports/{id}");
        EvaluatedIndividual<RestIndividual> aliceHolder = null;
        for (String d : keys) {
            Integer id = mapping.entrySet().stream().filter(e -> e.getValue().equals(d)).map(Map.Entry::getKey).findFirst().orElse(null);
            if (id == null) {
                System.out.println("  \"" + d + "\" not in IdMapper");
                continue;
            }
            List<EvaluatedIndividual<RestIndividual>> l = pops.get(id);
            System.out.println("  " + id + " \"" + d + "\" firstReachedAt=#" + firstStep.get(id) + " covered=" + archive.isCovered(id)
                + " popSize=" + (l == null ? 0 : l.size()));
            if (l != null) {
                for (EvaluatedIndividual<RestIndividual> e : l) {
                    System.out.println("      holder step#" + (e.getIndex() + 1) + " h=" + e.getFitness().getHeuristic(id) + " | " + calls(e));
                }
                if (d.startsWith("Auth:alice") && !l.isEmpty()) aliceHolder = l.get(0);
            }
        }
        if (aliceHolder != null) dumpFv("FV of holder of Auth:alice:PUT:/reports/{id}:2xx", aliceHolder, idMapper);
        System.exit(0);
    }
}
