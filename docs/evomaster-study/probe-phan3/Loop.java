import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.TypeLiteral;
import org.evomaster.core.EMConfig;
import org.evomaster.core.Main;
import org.evomaster.core.problem.enterprise.ExperimentalFaultCategory;
import org.evomaster.core.problem.enterprise.SampleType;
import org.evomaster.core.problem.httpws.auth.HttpWsAuthenticationInfo;
import org.evomaster.core.problem.rest.data.RestCallAction;
import org.evomaster.core.problem.rest.data.RestCallResult;
import org.evomaster.core.problem.rest.data.RestIndividual;
import org.evomaster.core.problem.rest.param.BodyParam;
import org.evomaster.core.problem.rest.service.sampler.RestSampler;
import org.evomaster.core.search.EvaluatedIndividual;
import org.evomaster.core.search.FitnessValue;
import org.evomaster.core.search.Heuristics;
import org.evomaster.core.search.action.ActionComponent;
import org.evomaster.core.search.algorithms.SmartsAlgorithm;
import org.evomaster.core.search.gene.utils.GeneUtils;
import org.evomaster.core.search.service.*;
import org.evomaster.core.search.service.time.SearchTimeController;
import java.lang.reflect.Field;
import java.util.*;
import java.util.stream.Collectors;

@SuppressWarnings({"unchecked", "rawtypes"})
public class Loop {

    static Object get(Object o, Class<?> owner, String name) throws Exception {
        Field f = owner.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(o);
    }

    static String call(RestCallAction a) {
        String body = "";
        for (Object p : a.getParameters()) {
            if (p instanceof BodyParam bp) {
                try {
                    body = " body=" + bp.primaryGene().getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false);
                } catch (Throwable t) {
                    body = " body=<" + t.getClass().getSimpleName() + ">";
                }
            }
        }
        return a.getAuth().getName() + " " + a.getVerb() + " " + a.resolvedPath() + body;
    }

    static String calls(RestIndividual ind) {
        return ind.seeMainExecutableActions().stream().map(x -> x.getAuth().getName() + " " + x.getName()).collect(Collectors.joining(" ; "));
    }

    static Integer status(EvaluatedIndividual<RestIndividual> ei, ActionComponent a) {
        Object r = ei.seeResult(a.getLocalId());
        return r == null ? null : ((RestCallResult) r).getStatusCode();
    }

    static void dumpFv(FitnessValue fv, IdMapper m) {
        List<Map.Entry<Integer, Heuristics>> es = new ArrayList<>(fv.getViewOfData().entrySet());
        es.sort((x, y) -> Integer.compare(y.getKey(), x.getKey()));
        for (Map.Entry<Integer, Heuristics> e : es) {
            System.out.println("      target " + e.getKey() + " score=" + e.getValue().getScore() + " actionIndex=" + e.getValue().getActionIndex() + " desc=\"" + m.getDescriptiveId(e.getKey()) + "\"");
        }
        System.out.println("      size=" + fv.getSize() + " computeFitnessScore()=" + fv.computeFitnessScore() + " coveredTargets=" + fv.coveredTargets().size() + " allTargets=" + fv.getViewOfData().size());
    }

    static void dumpPopulations(Archive<RestIndividual> archive, IdMapper m, String filter) throws Exception {
        Map<Integer, List<EvaluatedIndividual<RestIndividual>>> pops = (Map) get(archive, Archive.class, "populations");
        List<Integer> keys = new ArrayList<>(pops.keySet());
        keys.sort(Comparator.reverseOrder());
        for (Integer k : keys) {
            String d = m.getDescriptiveId(k);
            if (filter != null && !d.contains(filter)) continue;
            List<EvaluatedIndividual<RestIndividual>> l = pops.get(k);
            String members = l.stream().map(ei -> "[" + calls(ei.getIndividual()) + " h=" + ei.getFitness().getHeuristic(k) + "]").collect(Collectors.joining(" "));
            System.out.println("    pop " + k + " \"" + d + "\" covered=" + archive.isCovered(k) + " size=" + l.size() + " " + members);
        }
    }

    public static void main(String[] args) throws Exception {
        String thesis = "/Users/minhnguyen/IdeaProjects/graduational-thesis";
        String[] a = {"--blackBox", "true",
            "--bbSwaggerUrl", "http://localhost:8080/v3/api-docs", "--bbTargetUrl", "http://localhost:8080",
            "--configPath", thesis + "/infra/em-config/reports-auth.yaml",
            "--useExperimentalOracles", "true", "--extraPhaseBudgetPercentage", "0.6",
            "--outputFormat", "PYTHON_UNITTEST", "--ratePerMinute", "120", "--maxTime", "150s", "--seed", "5",
            "--outputFolder", args[0]};

        Injector inj = Main.init(a);
        EMConfig c = inj.getInstance(EMConfig.class);
        SmartsAlgorithm<RestIndividual> alg = inj.getInstance(Key.get(new TypeLiteral<SmartsAlgorithm<RestIndividual>>() {}));
        RestSampler sampler = (RestSampler) get(alg, SearchAlgorithm.class, "sampler");
        FitnessFunction<RestIndividual> ff = (FitnessFunction<RestIndividual>) get(alg, SearchAlgorithm.class, "ff");
        Archive<RestIndividual> archive = (Archive<RestIndividual>) get(alg, SearchAlgorithm.class, "archive");
        IdMapper idMapper = inj.getInstance(IdMapper.class);
        SearchTimeController time = inj.getInstance(SearchTimeController.class);
        AdaptiveParameterControl apc = inj.getInstance(AdaptiveParameterControl.class);
        Randomness randomness = inj.getInstance(Randomness.class);

        System.out.println("=== CONFIG");
        System.out.println("isUsingAdvancedTechniques()=" + c.isUsingAdvancedTechniques() + " isEnabledSmartSampling()=" + c.isEnabledSmartSampling()
            + " probOfSmartSampling=" + c.getProbOfSmartSampling() + " maxTestSize=" + c.getMaxTestSize() + " archiveTargetLimit=" + c.getArchiveTargetLimit()
            + " advancedBlackBoxCoverage=" + c.getAdvancedBlackBoxCoverage() + " blackBoxCleanUp=" + c.getBlackBoxCleanUp() + " statusOracles=" + c.getStatusOracles()
            + " feedbackDirectedSampling=" + c.getFeedbackDirectedSampling() + " focusedSearchActivationTime=" + c.getFocusedSearchActivationTime());
        System.out.println("same IdMapper in fitness? " + (get(ff, FitnessFunction.class, "idMapper") == idMapper) + " ; same IdMapper in archive? " + (get(archive, Archive.class, "idMapper") == idMapper));

        System.out.println("=== SAMPLER");
        System.out.println("numberOfDistinctActions()=" + sampler.numberOfDistinctActions());
        Map<String, Object> cluster = (Map) get(sampler, Sampler.class, "actionCluster");
        System.out.println("actionCluster keys (insertion order) = " + cluster.keySet());
        System.out.println("authentications = " + sampler.getAuthentications().getOfType(HttpWsAuthenticationInfo.class).stream().map(HttpWsAuthenticationInfo::getName).toList());
        List<RestIndividual> adhoc = sampler.getNotExecutedAdHocInitialIndividuals();
        System.out.println("getSizeOfAdHocInitialIndividuals()=" + sampler.getSizeOfAdHocInitialIndividuals());
        for (int i = 0; i < adhoc.size(); i++) {
            RestIndividual ind = adhoc.get(i);
            System.out.println("  adHoc[" + i + "] " + ind.getSampleType() + " size=" + ind.size() + " " + calls(ind));
        }
        System.out.println("hasSpecialInit()=" + sampler.hasSpecialInit());

        time.startSearch();
        System.out.println("=== LOOP over 36 ad-hoc tests: sample -> calculateCoverage -> addIfNeeded");
        List<EvaluatedIndividual<RestIndividual>> evaluated = new ArrayList<>();
        int k = 0;
        while (sampler.hasSpecialInit()) {
            k++;
            RestIndividual ind = sampler.sample(false);
            String what = ind.seeMainExecutableActions().stream().map(Loop::call).collect(Collectors.joining(" ; "));
            int before = time.getEvaluatedIndividuals();
            EvaluatedIndividual<RestIndividual> ei = ff.calculateCoverage(ind, Set.of(), null);
            int after = time.getEvaluatedIndividuals();
            evaluated.add(ei);
            RestCallAction main = ei.getIndividual().seeMainExecutableActions().get(0);
            String cleanup = ei.getIndividual().seeCleanUpActions().stream()
                .map(x -> ((RestCallAction) x).getVerb() + " " + ((RestCallAction) x).resolvedPath() + "->" + status(ei, x)).collect(Collectors.joining(","));
            int limit = apc.getArchiveTargetLimit();
            boolean added = archive.addIfNeeded(ei);
            System.out.println(String.format("#%02d sampleType=%s %s -> %s | cleanup=[%s] | targets=%d covered=%d | evaluatedIndividuals %d->%d | limit=%d addIfNeeded=%s | archive reached=%d covered=%d",
                k, ind.getSampleType(), what, status(ei, main), cleanup, ei.getFitness().getViewOfData().size(), ei.getFitness().coveredTargets().size(), before, after, limit, added,
                archive.numberOfReachedTargets(), archive.numberOfCoveredTargets()));
        }
        System.out.println("hasSpecialInit() after loop=" + sampler.hasSpecialInit());

        System.out.println("=== FITNESS of selected tests");
        for (int i = 0; i < evaluated.size(); i++) {
            EvaluatedIndividual<RestIndividual> ei = evaluated.get(i);
            String n = calls(ei.getIndividual());
            if (i == 0 || n.equals("bob POST:/reports") || n.equals("superadmin POST:/reports") || n.equals("NoAuth POST:/reports") || n.equals("superadmin GET:/users/me")) {
                System.out.println("  test #" + String.format("%02d", i + 1) + " " + n + " status=" + status(ei, ei.getIndividual().seeMainExecutableActions().get(0)));
                dumpFv(ei.getFitness(), idMapper);
            }
        }

        System.out.println("=== ARCHIVE populations for /reports POST and /users/me");
        dumpPopulations(archive, idMapper, "POST:/reports");
        dumpPopulations(archive, idMapper, "GET:/users/me");
        System.out.println("notCoveredTargets = " + archive.notCoveredTargets().stream().sorted(Comparator.reverseOrder()).map(t -> t + "=\"" + idMapper.getDescriptiveId(t) + "\"").toList());

        System.out.println("=== DEMO longer test on covered target");
        List<HttpWsAuthenticationInfo> auths = sampler.getAuthentications().getOfType(HttpWsAuthenticationInfo.class);
        HttpWsAuthenticationInfo superadmin = auths.stream().filter(x -> x.getName().equals("superadmin")).findFirst().get();
        RestCallAction me1 = (RestCallAction) ((RestCallAction) cluster.get("GET:/users/me")).copy();
        RestCallAction me2 = (RestCallAction) ((RestCallAction) cluster.get("GET:/users/me")).copy();
        me1.doInitialize(randomness);
        me2.doInitialize(randomness);
        me1.setAuth(superadmin);
        me2.setAuth(superadmin);
        RestIndividual two = sampler.createIndividual(SampleType.SMART, new ArrayList<>(List.of(me1, me2)));
        EvaluatedIndividual<RestIndividual> eiTwo = ff.calculateCoverage(two, Set.of(), null);
        System.out.println("  two-call test " + calls(two) + " statuses " + eiTwo.getIndividual().seeMainExecutableActions().stream().map(x -> String.valueOf(status(eiTwo, x))).toList());
        dumpFv(eiTwo.getFitness(), idMapper);
        System.out.println("  addIfNeeded=" + archive.addIfNeeded(eiTwo));
        dumpPopulations(archive, idMapper, "GET:/users/me");

        System.out.println("=== calculateCoverage vs computeWholeAchievedCoverageForPostProcessing");
        RestIndividual probe = (RestIndividual) evaluated.get(0).getIndividual().copy();
        probe.removeAllCleanUp();
        int i0 = time.getEvaluatedIndividuals();
        int a0 = time.getEvaluatedActions();
        EvaluatedIndividual<RestIndividual> e1 = ff.calculateCoverage((RestIndividual) probe.copy(), Set.of(), null);
        int i1 = time.getEvaluatedIndividuals();
        int a1 = time.getEvaluatedActions();
        EvaluatedIndividual<RestIndividual> e2 = ff.computeWholeAchievedCoverageForPostProcessing((RestIndividual) probe.copy());
        int i2 = time.getEvaluatedIndividuals();
        int a2 = time.getEvaluatedActions();
        System.out.println("  test " + calls(probe));
        System.out.println("  calculateCoverage: evaluatedIndividuals " + i0 + "->" + i1 + " evaluatedActions " + a0 + "->" + a1 + " targets=" + e1.getFitness().getViewOfData().size());
        System.out.println("  computeWholeAchievedCoverageForPostProcessing: evaluatedIndividuals " + i1 + "->" + i2 + " evaluatedActions " + a1 + "->" + a2 + " targets=" + e2.getFitness().getViewOfData().size());
        System.out.println("  same target ids? " + e1.getFitness().getViewOfData().keySet().equals(e2.getFitness().getViewOfData().keySet()));

        System.out.println("=== sampleIndividual x5");
        for (int j = 0; j < 5; j++) {
            EvaluatedIndividual<RestIndividual> s = archive.sampleIndividual();
            System.out.println("  populationOrigin=\"" + s.getIndividual().getPopulationOrigin() + "\" test=" + calls(s.getIndividual()));
        }

        System.out.println("=== extractSolution");
        List<EvaluatedIndividual<RestIndividual>> sol = archive.extractSolution().getIndividuals();
        System.out.println("  individuals=" + sol.size() + " ; archive reached=" + archive.numberOfReachedTargets() + " covered=" + archive.numberOfCoveredTargets() + " notCovered=" + archive.notCoveredTargets().size());
        Map<Integer, List<EvaluatedIndividual<RestIndividual>>> pops = (Map) get(archive, Archive.class, "populations");
        for (EvaluatedIndividual<RestIndividual> ei : sol) {
            List<String> mine = new ArrayList<>();
            for (Map.Entry<Integer, List<EvaluatedIndividual<RestIndividual>>> e : pops.entrySet()) {
                if (archive.isCovered(e.getKey()) && e.getValue().get(0) == ei) mine.add(idMapper.getDescriptiveId(e.getKey()));
            }
            System.out.println("  " + calls(ei.getIndividual()) + " holds " + mine.size() + " covered targets: " + mine);
        }

        System.out.println("=== fault target naming");
        String d = idMapper.getFaultDescriptiveId(ExperimentalFaultCategory.SECURITY_STATEFUL_AUTHORIZATION, "POST:/reports");
        System.out.println("  getFaultDescriptiveId(970, \"POST:/reports\") = \"" + d + "\" isFault=" + IdMapper.Companion.isFault(d));
        int id = idMapper.handleLocalTarget(d);
        System.out.println("  handleLocalTarget -> " + id + " ; again -> " + idMapper.handleLocalTarget(d) + " ; idMapper.isFault(id)=" + idMapper.isFault(id));
        System.exit(0);
    }
}
