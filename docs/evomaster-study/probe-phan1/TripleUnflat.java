import org.evomaster.core.EMConfig;
import org.evomaster.core.problem.rest.schema.*;
import org.evomaster.core.problem.rest.builder.RestActionBuilderV3;
import org.evomaster.core.problem.rest.data.*;
import org.evomaster.core.problem.api.param.Param;
import org.evomaster.core.problem.httpws.auth.*;
import org.evomaster.core.problem.enterprise.SampleType;
import org.evomaster.core.search.*;
import org.evomaster.core.search.action.*;
import org.evomaster.core.search.gene.Gene;
import org.evomaster.core.search.gene.utils.GeneUtils;
import org.evomaster.core.search.service.Randomness;
import java.nio.file.*;
import java.util.*;

public class TripleUnflat {
    static void top(RestIndividual ind) {
        StringBuilder sb = new StringBuilder();
        for (StructuralElement c : ind.getViewOfChildren()) {
            sb.append(c.getClass().getSimpleName()).append("(").append(c.getLocalId()).append(") ");
        }
        System.out.println("   children: " + sb);
    }
    static void mains(String label, RestIndividual ind) {
        StringBuilder sb = new StringBuilder();
        for (RestCallAction a : ind.seeMainExecutableActions()) {
            sb.append("[").append(a.getLocalId()).append(" ").append(a.getName()).append(" auth=").append(a.getAuth().getName()).append("] ");
        }
        System.out.println(label + " seeMainExecutableActions = " + sb);
    }
    static void set(RestCallAction a, String n, String v) {
        for (Gene g : a.seeAllGenes()) if (g.getName().equals(n) && g.getViewOfChildren().isEmpty()) { g.setFromStringValue(v, true); return; }
    }
    static HttpWsAuthenticationInfo auth(String name) {
        return new HttpWsAuthenticationInfo(name, List.of(new AuthenticationHeader("Authorization", "Bearer x")), null, false, null);
    }
    static String body(RestCallAction a) {
        for (Param p : a.getParameters()) if (p instanceof org.evomaster.core.problem.rest.param.BodyParam) return p.primaryGene().getValueAsRawString();
        return "-";
    }
    public static void main(String[] args) throws Exception {
        SchemaOpenAPI s = OpenApiAccess.INSTANCE.parseOpenApi(Files.readString(Path.of(args[0])), SchemaLocation.Companion.getMEMORY());
        EMConfig cfg = new EMConfig(); cfg.setBlackBox(true);
        Map<String, Action> cluster = new LinkedHashMap<>();
        RestActionBuilderV3.INSTANCE.addActionsFromSwagger(new RestSchema(s), cluster, List.of(), new RestActionBuilderV3.Options(cfg));
        Randomness randomness = new Randomness();

        RestCallAction src0 = (RestCallAction) cluster.get("POST:/reports").copy();
        src0.doInitialize(randomness);
        set(src0, "title", "8nI4Cb1ZO"); set(src0, "classification", "PUBLIC");
        src0.setAuth(auth("superadmin"));
        RestIndividual victimSlice = new RestIndividual(new ArrayList<>(List.of(src0)), SampleType.SMART, new ArrayList<>(), null, -1);
        victimSlice.doInitializeLocalId();
        System.out.println("victimSlice sampleType=" + victimSlice.getSampleType()); top(victimSlice); mains("victimSlice", victimSlice);

        RestCallAction transitionDef = (RestCallAction) cluster.get("PUT:/users/{username}/role");
        HttpWsAuthenticationInfo operator = auth("bob");

        System.out.println("958 base = victimSlice.copy()");
        RestIndividual base = (RestIndividual) victimSlice.copy();
        System.out.println("   base==victimSlice? " + (base == victimSlice)); mains("   base", base);
        System.out.println("959 source = base.seeMainExecutableActions().last()");
        RestCallAction source = base.seeMainExecutableActions().get(base.seeMainExecutableActions().size() - 1);
        System.out.println("   source=" + source.getName() + " localId=" + source.getLocalId() + " body=" + body(source));
        System.out.println("960 victimAuth = source.auth");
        HttpWsAuthenticationInfo victimAuth = source.getAuth();
        System.out.println("   victimAuth.name=" + victimAuth.getName());
        System.out.println("962 transition = transitionDef.copy()");
        RestCallAction transition = (RestCallAction) transitionDef.copy();
        System.out.println("   transition=" + transition.getName() + " localId=" + transition.getLocalId() + " initialized=" + transition.isInitialized() + " auth=" + transition.getAuth().getName());
        System.out.println("963 transition.resetLocalIdRecursively()");
        transition.resetLocalIdRecursively();
        System.out.println("   localId=" + transition.getLocalId());
        transition.forceNewTaints();
        System.out.println("965 transition.doInitialize(randomness)");
        transition.doInitialize(randomness);
        System.out.println("   initialized=" + transition.isInitialized() + " resolvedPath=" + transition.resolvedPath() + " body=" + body(transition));
        System.out.println("966 transition.auth = operator");
        transition.setAuth(operator);
        System.out.println("   auth=" + transition.getAuth().getName());
        set(transition, "username", victimAuth.getName()); set(transition, "role", "VIEWER");
        System.out.println("967-977 (setUserTargetToVictim, setRoleFieldToReduced) -> resolvedPath=" + transition.resolvedPath() + " body=" + body(transition));
        System.out.println("978 base.addMainActionInEmptyEnterpriseGroup(action = transition)");
        base.addMainActionInEmptyEnterpriseGroup(-1, transition);
        top(base); mains("   base", base);
        System.out.println("980 followUp = source.copy()");
        RestCallAction followUp = (RestCallAction) source.copy();
        System.out.println("   followUp localId=" + followUp.getLocalId() + " (source " + source.getLocalId() + ") same object? " + (followUp == source) + " auth=" + followUp.getAuth().getName() + " auth same object as source? " + (followUp.getAuth() == source.getAuth()) + " body=" + body(followUp));
        System.out.println("981 followUp.resetLocalIdRecursively()");
        followUp.resetLocalIdRecursively();
        System.out.println("   localId=" + followUp.getLocalId());
        followUp.forceNewTaints();
        System.out.println("984 base.addMainActionInEmptyEnterpriseGroup(action = followUp)");
        base.addMainActionInEmptyEnterpriseGroup(-1, followUp);
        top(base); mains("   base", base);
        System.out.println("986 base.doInitializeLocalId()");
        base.doInitializeLocalId();
        top(base); mains("   base", base);
        System.out.println("987 base.modifySampleType(SampleType.SECURITY)  before=" + base.getSampleType());
        base.modifySampleType(SampleType.SECURITY);
        System.out.println("   after=" + base.getSampleType());
        System.out.println("988 base.ensureFlattenedStructure()");
        boolean r = base.ensureFlattenedStructure();
        System.out.println("   returned " + r); top(base); mains("   base", base);
        base.fixResourceForwardLinks();
        System.out.println("victimSlice unchanged: "); top(victimSlice); mains("   victimSlice", victimSlice);

        int[] codes = {201, 200, 201};
        List<ActionResult> results = new ArrayList<>();
        List<RestCallAction> main = base.seeMainExecutableActions();
        for (int i = 0; i < 3; i++) { RestCallResult res = new RestCallResult(main.get(i).getLocalId(), false); res.setStatusCode(codes[i]); results.add(res); }
        EvaluatedIndividual<RestIndividual> ei = new EvaluatedIndividual<>(new FitnessValue(3.0), base, results, null, -1, (org.evomaster.core.search.impact.impactinfocollection.ImpactsOfIndividual) null);
        for (RestCallAction a : main) {
            ActionResult res = ei.seeResult(a.getLocalId());
            System.out.println("statusIn(ei, " + a.getName() + " " + a.getLocalId() + "): result class=" + res.getClass().getSimpleName() + " is RestCallResult=" + (res instanceof RestCallResult) + " -> " + ((RestCallResult) res).getStatusCode());
        }
        ActionResult plain = new ActionResult(main.get(0).getLocalId(), false, false);
        System.out.println("plain ActionResult is RestCallResult? " + (plain instanceof RestCallResult));
        RestCallResult nostatus = new RestCallResult(main.get(0).getLocalId(), false);
        System.out.println("RestCallResult without setStatusCode -> getStatusCode()=" + nostatus.getStatusCode());
    }
}
