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

public class Dump {

    static void tree(StructuralElement e, String indent) {
        String extra = "";
        if (e instanceof Param p) extra = " name=" + p.getName();
        if (e instanceof Gene g) {
            extra = " name=" + g.getName();
            try {
                extra += " value=" + g.getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false);
            } catch (Throwable t) {
                extra += " value=<" + t.getClass().getSimpleName() + ">";
            }
        }
        String id = e.hasLocalId() ? " localId=" + e.getLocalId() : "";
        System.out.println(indent + e.getClass().getSimpleName() + extra + id);
        for (StructuralElement c : e.getViewOfChildren()) tree(c, indent + "    ");
    }

    static void set(RestCallAction a, String geneName, String value) {
        for (Gene g : a.seeAllGenes()) {
            if (g.getName().equals(geneName) && g.getViewOfChildren().isEmpty()) {
                boolean ok = g.setFromStringValue(value, true);
                System.out.println("set " + a.getName() + " " + geneName + "=" + value + " ok=" + ok + " gene=" + g.getClass().getSimpleName());
                return;
            }
        }
        System.out.println("NOT FOUND " + geneName);
    }

    static HttpWsAuthenticationInfo auth(String name) {
        return new HttpWsAuthenticationInfo(name, List.of(new AuthenticationHeader("Authorization", "Bearer x")), null, false, null);
    }

    public static void main(String[] args) throws Exception {
        String text = Files.readString(Path.of(args[0]));
        SchemaOpenAPI s = OpenApiAccess.INSTANCE.parseOpenApi(text, SchemaLocation.Companion.getMEMORY());
        EMConfig cfg = new EMConfig();
        cfg.setBlackBox(true);
        Map<String, Action> cluster = new LinkedHashMap<>();
        RestActionBuilderV3.INSTANCE.addActionsFromSwagger(new RestSchema(s), cluster, List.of(), new RestActionBuilderV3.Options(cfg));
        System.out.println("cluster keys = " + cluster.keySet());

        RestCallAction post = (RestCallAction) cluster.get("POST:/reports");
        RestCallAction put = (RestCallAction) cluster.get("PUT:/users/{username}/role");
        System.out.println("=== template POST:/reports (chua initialize)");
        tree(post, "");
        System.out.println("=== template PUT:/users/{username}/role (chua initialize)");
        tree(put, "");

        Randomness r = new Randomness();
        RestCallAction a1 = (RestCallAction) post.copy();
        RestCallAction a2 = (RestCallAction) put.copy();
        RestCallAction a3 = (RestCallAction) post.copy();
        a1.doInitialize(r);
        a2.doInitialize(r);
        a3.doInitialize(r);
        System.out.println("=== a1 sau doInitialize(random seed 42)");
        tree(a1, "");
        set(a1, "title", "8nI4Cb1ZO");
        set(a1, "classification", "PUBLIC");
        set(a2, "username", "superadmin");
        set(a2, "role", "VIEWER");
        set(a3, "title", "8nI4Cb1ZO");
        set(a3, "classification", "PUBLIC");
        a1.setAuth(auth("superadmin"));
        a2.setAuth(auth("bob"));
        a3.setAuth(auth("superadmin"));

        List<Action> actions = new ArrayList<>(List.of(a1, a2, a3));
        RestIndividual ind = new RestIndividual(actions, SampleType.SECURITY, new ArrayList<>(), null, -1);
        ind.doInitializeLocalId();
        System.out.println("=== RestIndividual");
        tree(ind, "");
        System.out.println("=== seeMainExecutableActions");
        for (RestCallAction a : ind.seeMainExecutableActions()) {
            System.out.println(a.getLocalId() + " | getName()=" + a.getName() + " | verb=" + a.getVerb() + " | path=" + a.getPath() + " | resolvedPath()=" + a.resolvedPath() + " | auth.name=" + a.getAuth().getName() + " | parameters=" + a.getParameters().stream().map(p -> p.getClass().getSimpleName() + "(" + p.getName() + ")").toList() + " | toString=" + a);
            for (Param p : a.getParameters()) {
                Gene g = p.primaryGene();
                System.out.println("    " + p.getClass().getSimpleName() + " primaryGene=" + g.getClass().getSimpleName() + " raw=" + g.getValueAsRawString() + " | JSON=" + g.getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false));
            }
        }
        System.out.println("size()=" + ind.size() + " seeAllActions().size=" + ind.seeAllActions().size());

        int[] codes = {201, 200, 201};
        List<ActionResult> results = new ArrayList<>();
        List<RestCallAction> main = ind.seeMainExecutableActions();
        for (int i = 0; i < 3; i++) {
            RestCallResult res = new RestCallResult(main.get(i).getLocalId(), false);
            res.setStatusCode(codes[i]);
            results.add(res);
        }
        ((RestCallResult) results.get(0)).setBody("{\"title\":\"8nI4Cb1ZO\",\"owner\":\"superadmin\",\"classification\":\"PUBLIC\"}");
        EvaluatedIndividual<RestIndividual> ei = new EvaluatedIndividual<>(new FitnessValue(3.0), ind, results, null, -1, (org.evomaster.core.search.impact.impactinfocollection.ImpactsOfIndividual) null);
        System.out.println("=== EvaluatedIndividual");
        for (RestCallAction a : main) {
            RestCallResult rr = (RestCallResult) ei.seeResult(a.getLocalId());
            System.out.println("seeResult(" + a.getLocalId() + ") -> sourceLocalId=" + rr.getSourceLocalId() + " getStatusCode()=" + rr.getStatusCode() + " getBody()=" + rr.getBody() + " stopping=" + rr.getStopping());
        }
        for (EvaluatedAction ea : ei.evaluatedMainActions()) {
            System.out.println("evaluatedMainActions: " + ea.getAction().getName() + " -> " + ((RestCallResult) ea.getResult()).getStatusCode());
        }
        System.out.println("seeResult(\"ACTION_COMPONENT_99\") -> " + ei.seeResult("ACTION_COMPONENT_99"));

        RestIndividual cp = (RestIndividual) ind.copy();
        System.out.println("=== copy");
        System.out.println("copy same object? " + (cp == ind) + " ; first action same object? " + (cp.seeMainExecutableActions().get(0) == ind.seeMainExecutableActions().get(0)) + " ; localId copy=" + cp.seeMainExecutableActions().get(0).getLocalId());
        cp.resetLocalIdRecursively();
        System.out.println("after resetLocalIdRecursively: " + cp.seeMainExecutableActions().get(0).getLocalId() + " ; original still " + ind.seeMainExecutableActions().get(0).getLocalId());
    }
}
