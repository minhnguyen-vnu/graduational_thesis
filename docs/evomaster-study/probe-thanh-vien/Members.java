import com.webfuzzing.commons.faults.FaultCategory;
import org.evomaster.client.java.controller.api.dto.auth.AuthenticationDto;
import org.evomaster.core.EMConfig;
import org.evomaster.core.config.ConfigUtil;
import org.evomaster.core.config.ConfigsFromFile;
import org.evomaster.core.problem.api.param.Param;
import org.evomaster.core.problem.enterprise.DetectedFault;
import org.evomaster.core.problem.enterprise.DetectedFaultUtils;
import org.evomaster.core.problem.enterprise.ExperimentalFaultCategory;
import org.evomaster.core.problem.enterprise.SampleType;
import org.evomaster.core.problem.enterprise.auth.AuthSettings;
import org.evomaster.core.problem.enterprise.auth.NoAuth;
import org.evomaster.core.problem.httpws.auth.*;
import org.evomaster.core.problem.rest.StatusGroup;
import org.evomaster.core.problem.rest.builder.RestActionBuilderV3;
import org.evomaster.core.problem.rest.builder.RestIndividualSelectorUtils;
import org.evomaster.core.problem.rest.data.*;
import org.evomaster.core.problem.rest.param.*;
import org.evomaster.core.problem.rest.schema.*;
import org.evomaster.core.problem.rest.service.RestSecurityBuilder;
import org.evomaster.core.search.*;
import org.evomaster.core.search.action.*;
import org.evomaster.core.search.gene.*;
import org.evomaster.core.search.gene.collection.*;
import org.evomaster.core.search.gene.utils.GeneUtils;
import org.evomaster.core.search.gene.wrapper.*;
import org.evomaster.core.search.service.IdMapper;
import org.evomaster.core.search.service.Randomness;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class Members {

    static final String[] CLASSES = {
        "org.evomaster.core.search.service.Archive",
        "org.evomaster.core.search.Solution",
        "org.evomaster.core.search.EvaluatedIndividual",
        "org.evomaster.core.search.action.EvaluatedAction",
        "org.evomaster.core.problem.rest.builder.RestIndividualSelectorUtils",
        "org.evomaster.core.search.service.FitnessFunction",
        "org.evomaster.core.problem.rest.data.RestIndividual",
        "org.evomaster.core.problem.api.ApiWsIndividual",
        "org.evomaster.core.problem.enterprise.EnterpriseIndividual",
        "org.evomaster.core.search.Individual",
        "org.evomaster.core.problem.rest.data.RestCallAction",
        "org.evomaster.core.problem.httpws.HttpWsAction",
        "org.evomaster.core.problem.api.ApiWsAction",
        "org.evomaster.core.search.action.MainAction",
        "org.evomaster.core.search.action.Action",
        "org.evomaster.core.search.action.ActionComponent",
        "org.evomaster.core.search.StructuralElement",
        "org.evomaster.core.problem.rest.data.RestPath",
        "org.evomaster.core.problem.rest.data.HttpVerb",
        "org.evomaster.core.problem.rest.StatusGroup",
        "org.evomaster.core.problem.enterprise.SampleType",
        "org.evomaster.core.problem.rest.data.RestCallResult",
        "org.evomaster.core.problem.httpws.HttpWsCallResult",
        "org.evomaster.core.problem.enterprise.EnterpriseActionResult",
        "org.evomaster.core.search.action.ActionResult",
        "org.evomaster.core.problem.api.param.Param",
        "org.evomaster.core.problem.rest.param.BodyParam",
        "org.evomaster.core.problem.rest.param.PathParam",
        "org.evomaster.core.problem.rest.param.QueryParam",
        "org.evomaster.core.search.gene.Gene",
        "org.evomaster.core.search.gene.ObjectGene",
        "org.evomaster.core.search.gene.collection.ArrayGene",
        "org.evomaster.core.search.gene.collection.EnumGene",
        "org.evomaster.core.search.gene.wrapper.SelectableWrapperGene",
        "org.evomaster.core.search.gene.wrapper.OptionalGene",
        "org.evomaster.core.search.gene.wrapper.NullableGene",
        "org.evomaster.core.search.gene.wrapper.ChoiceGene",
        "org.evomaster.core.search.gene.wrapper.CustomMutationRateGene",
        "org.evomaster.core.problem.enterprise.auth.AuthenticationInfo",
        "org.evomaster.core.problem.httpws.auth.HttpWsAuthenticationInfo",
        "org.evomaster.core.problem.httpws.auth.HttpWsNoAuth",
        "org.evomaster.core.problem.enterprise.auth.AuthSettings",
        "org.evomaster.core.problem.httpws.auth.EndpointCallLogin",
        "org.evomaster.core.problem.httpws.auth.CallToEndpoint",
        "org.evomaster.core.search.FitnessValue",
        "org.evomaster.core.search.service.IdMapper",
        "org.evomaster.core.problem.enterprise.DetectedFault",
        "org.evomaster.core.problem.enterprise.DetectedFaultUtils",
        "org.evomaster.core.problem.enterprise.ExperimentalFaultCategory",
        "org.evomaster.core.EMConfig",
    };

    static String simple(Type t) {
        return t.getTypeName().replaceAll("[a-z][a-zA-Z0-9_]*\\.", "").replace("$", ".");
    }

    static void fields() throws Exception {
        for (String n : CLASSES) {
            Class<?> c = Class.forName(n);
            String sup = c.getSuperclass() == null ? "-" : c.getSuperclass().getSimpleName();
            List<Field> fs = Arrays.stream(c.getDeclaredFields())
                    .filter(f -> !Modifier.isStatic(f.getModifiers()) && !f.isSynthetic() && !f.getName().contains("$"))
                    .collect(Collectors.toList());
            long own = Arrays.stream(c.getDeclaredMethods())
                    .filter(m -> Modifier.isPublic(m.getModifiers()) && !m.isSynthetic() && !m.isBridge() && !m.getName().contains("$"))
                    .count();
            long all = Arrays.stream(c.getMethods()).filter(m -> !m.isSynthetic() && !m.isBridge() && !m.getName().contains("$")).count();
            System.out.printf("== %s extends %s | fields=%d | public methods declared=%d, public incl. inherited=%d%n",
                    c.getSimpleName(), sup, fs.size(), own, all);
            if (c.getSimpleName().equals("EMConfig")) continue;
            for (Field f : fs) System.out.println("   " + f.getName() + " : " + simple(f.getGenericType()));
        }
    }

    static String acts(RestIndividual ind) {
        StringBuilder sb = new StringBuilder();
        for (RestCallAction a : ind.seeMainExecutableActions()) {
            sb.append("[").append(a.getLocalId()).append(" ").append(a.getName()).append(" auth=").append(a.getAuth().getName()).append("] ");
        }
        return sb.toString().trim();
    }

    static String body(RestCallAction a) {
        for (Param p : a.getParameters()) {
            if (p instanceof BodyParam) return p.primaryGene().getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false);
        }
        return "-";
    }

    static <T> T first(StructuralElement e, Class<T> k) {
        if (k.isInstance(e)) return k.cast(e);
        List<StructuralElement> ch = new ArrayList<>(e.getViewOfChildren());
        if (e instanceof ArrayGene) ch.add(((ArrayGene<?>) e).getTemplate());
        for (StructuralElement c : ch) {
            T r = first(c, k);
            if (r != null) return r;
        }
        return null;
    }

    static Gene leaf(Gene g) {
        while (g instanceof org.evomaster.core.search.gene.interfaces.WrapperGene) {
            List<Gene> ch = g.getViewOfChildren();
            g = (g instanceof ChoiceGene) ? ch.get(ch.size() - 1) : ch.get(0);
        }
        return g;
    }

    static String chain(Gene g) {
        List<String> parts = new ArrayList<>();
        StructuralElement p = g;
        while (p != null) {
            String s = p.getClass().getSimpleName();
            if (p instanceof Gene) s += "(" + ((Gene) p).getName() + ")";
            if (p instanceof Param) s += "(" + ((Param) p).getName() + ")";
            if (p instanceof SelectableWrapperGene) s += "[isActive=" + ((SelectableWrapperGene) p).isActive() + "]";
            if (p instanceof ChoiceGene) s += "[activeGeneIndex=" + ((ChoiceGene<?>) p).getActiveGeneIndex() + "]";
            parts.add(s);
            if (p instanceof RestCallAction) break;
            p = p.getParent();
        }
        return String.join(" <- ", parts);
    }

    static Map<String, Action> load(String spec) throws Exception {
        SchemaOpenAPI s = OpenApiAccess.INSTANCE.parseOpenApi(Files.readString(Path.of(spec)), SchemaLocation.Companion.getMEMORY());
        EMConfig cfg = new EMConfig();
        cfg.setBlackBox(true);
        Map<String, Action> cluster = new LinkedHashMap<>();
        RestActionBuilderV3.INSTANCE.addActionsFromSwagger(new RestSchema(s), cluster, List.of(), new RestActionBuilderV3.Options(cfg));
        return cluster;
    }

    static String mask(String payload) {
        return payload == null ? null : payload.replaceAll("(\"password\"\\s*:\\s*\")[^\"]*(\")", "$1***$2");
    }

    public static void main(String[] args) throws Exception {
        String reportsSpec = args[0], authYaml = args[1], vampiSpec = args[2], akSpec = args[3], pyloadSpec = args[4];

        System.out.println("##### A. thuoc tinh (field) khai bao trong tung lop, jar TR2");
        fields();

        System.out.println("##### B. dang nhap: " + authYaml);
        ConfigsFromFile cf = ConfigUtil.INSTANCE.readFromFile(authYaml);
        cf.validateAndNormalizeAuth();
        List<HttpWsAuthenticationInfo> infos = new ArrayList<>();
        for (AuthenticationDto d : cf.getAuth()) infos.add(HttpWsAuthenticationInfo.Companion.fromDto(d, null));
        for (HttpWsAuthenticationInfo i : infos) {
            EndpointCallLogin l = i.getEndpointCallLogin();
            CallToEndpoint c = l.getCall();
            System.out.println("auth name=" + i.getName() + " headers=" + i.getHeaders().size() + " requireMockHandling=" + i.getRequireMockHandling()
                    + " | endpointCallLogin.name=" + l.getName() + " call.verb=" + c.getVerb() + " call.endpoint=" + c.getEndpoint()
                    + " call.contentType=" + c.getContentType() + " call.payload=" + mask(c.getPayload()) + " token=" + (l.getToken() != null));
        }
        HttpWsAuthenticationInfo alice = infos.get(0), superadmin = infos.get(1), bob = infos.get(2);
        AuthSettings settings = new AuthSettings(new ArrayList<>(infos));
        System.out.println("AuthSettings.size()=" + settings.size());
        System.out.println("getAllOthers(\"alice\", HttpWsAuthenticationInfo) = "
                + settings.getAllOthers("alice", HttpWsAuthenticationInfo.class).stream().map(HttpWsAuthenticationInfo::getName).collect(Collectors.toList()));
        try {
            settings.getAllOthers("mallory", HttpWsAuthenticationInfo.class);
        } catch (IllegalArgumentException e) {
            System.out.println("getAllOthers(\"mallory\", ...) -> IllegalArgumentException: " + e.getMessage());
        }
        System.out.println("alice.isDifferentFrom(superadmin)=" + alice.isDifferentFrom(superadmin) + " alice.isDifferentFrom(alice)=" + alice.isDifferentFrom(alice));
        HttpWsNoAuth na = new HttpWsNoAuth();
        System.out.println("HttpWsNoAuth name=" + na.getName() + " is NoAuth=" + (na instanceof NoAuth) + " is HttpWsAuthenticationInfo=" + (na instanceof HttpWsAuthenticationInfo)
                + " alice is NoAuth=" + (((Object) alice) instanceof NoAuth));

        System.out.println("##### C. RestCallAction tu spec: " + reportsSpec);
        Map<String, Action> cluster = load(reportsSpec);
        List<RestCallAction> defs = cluster.values().stream().map(a -> (RestCallAction) a).collect(Collectors.toList());
        System.out.println("so action definitions=" + defs.size());
        System.out.println("getAllActionDefinitions(defs, PUT) = " + RestIndividualSelectorUtils.INSTANCE.getAllActionDefinitions(defs, HttpVerb.PUT).stream().map(RestCallAction::getName).collect(Collectors.toList()));
        RestCallAction srcDef = (RestCallAction) cluster.get("PUT:/reports/{id}");
        RestCallAction tDef = (RestCallAction) cluster.get("PUT:/users/{username}/role");
        for (RestCallAction d : List.of(srcDef, tDef)) {
            System.out.println("def " + d.getName() + " | id=" + d.getId() + " verb=" + d.getVerb() + " path=" + d.getPath() + " (" + d.getPath().getClass().getSimpleName() + ")"
                    + " auth=" + d.getAuth().getName() + " localId=" + d.getLocalId() + " initialized=" + d.isInitialized()
                    + " parameters=" + d.getParameters().stream().map(p -> p.getClass().getSimpleName() + "(" + p.getName() + ")").collect(Collectors.toList()));
            for (Param p : d.getParameters()) {
                System.out.println("   param " + p.getClass().getSimpleName() + " name=" + p.getName() + " primaryGene()=" + p.primaryGene().getClass().getSimpleName() + "(" + p.primaryGene().getName() + ")"
                        + " gene=" + p.getGene().getClass().getSimpleName() + " sameAsPrimary=" + (p.getGene() == p.primaryGene()));
            }
            System.out.println("   looksLikePermissionReducingTransition=" + RestSecurityBuilder.Companion.looksLikePermissionReducingTransition(d));
        }

        System.out.println("##### D. lap bo ba nhu B:958-990 (nguon PUT:/reports/{id}, nan nhan alice, nguoi ha superadmin, nhu log seed 2 dong 534)");
        Randomness r = new Randomness();
        RestCallAction src = (RestCallAction) srcDef.copy();
        src.doInitialize(r);
        src.setAuth(alice);
        RestIndividual victimSlice = new RestIndividual(new ArrayList<>(List.of(src)), SampleType.SMART, new ArrayList<>(), null, -1);
        victimSlice.doInitializeLocalId();
        victimSlice.ensureFlattenedStructure();
        System.out.println("victimSlice sampleType=" + victimSlice.getSampleType() + " size()=" + victimSlice.size() + " actions=" + acts(victimSlice));

        RestIndividual base = (RestIndividual) victimSlice.copy();
        System.out.println("958 base = victimSlice.copy() -> same object? " + (base == victimSlice) + " actions=" + acts(base));
        RestCallAction source = base.seeMainExecutableActions().get(base.seeMainExecutableActions().size() - 1);
        System.out.println("959 source = base.seeMainExecutableActions().last() -> " + source.getName() + " localId=" + source.getLocalId() + " resolvedPath=" + source.resolvedPath() + " body=" + body(source));
        HttpWsAuthenticationInfo victimAuth = source.getAuth();
        System.out.println("960 victimAuth = source.auth -> " + victimAuth.getName());
        RestCallAction transition = (RestCallAction) tDef.copy();
        System.out.println("962 transition = transitionDef.copy() -> localId=" + transition.getLocalId() + " initialized=" + transition.isInitialized() + " auth=" + transition.getAuth().getName());
        transition.resetLocalIdRecursively();
        System.out.println("963 resetLocalIdRecursively -> localId=" + transition.getLocalId());
        transition.forceNewTaints();
        System.out.println("964 forceNewTaints -> ok");
        transition.doInitialize(r);
        System.out.println("965 doInitialize(randomness) -> initialized=" + transition.isInitialized() + " resolvedPath=" + transition.resolvedPath() + " body=" + body(transition));
        transition.setAuth(superadmin);
        System.out.println("966 transition.auth = operator -> " + transition.getAuth().getName());

        Gene userLeaf = leaf(transition.getParameters().stream().filter(p -> p instanceof PathParam).findFirst().get().primaryGene());
        ObjectGene roleObj = (ObjectGene) transition.getParameters().stream().filter(p -> p instanceof BodyParam).findFirst().get().primaryGene();
        System.out.println("ObjectGene(body).fields = " + roleObj.getFields().stream().map(g -> g.getClass().getSimpleName() + "(" + g.getName() + ")").collect(Collectors.toList()));
        EnumGene<?> role = (EnumGene<?>) roleObj.getFields().get(0);
        System.out.println("role EnumGene values=" + role.getValues() + " index=" + role.getIndex() + " raw=" + role.getValueAsRawString());
        System.out.println("chain(username leaf) = " + chain(userLeaf));
        System.out.println("chain(role) = " + chain(role));
        System.out.println("CustomMutationRateGene(username).getViewOfChildren() = " + userLeaf.getParent() + " children="
                + ((Gene) userLeaf.getParent()).getViewOfChildren().stream().map(g -> g.getClass().getSimpleName()).collect(Collectors.toList()));
        System.out.println("username.setFromStringValue(\"alice\", true) -> " + userLeaf.setFromStringValue("alice", true) + " raw=" + userLeaf.getValueAsRawString());
        System.out.println("role.setFromStringValue(\"VIEWER\", true) -> " + role.setFromStringValue("VIEWER", true) + " index=" + role.getIndex() + " raw=" + role.getValueAsRawString());
        System.out.println("967-977 sau khi dat truong -> resolvedPath=" + transition.resolvedPath() + " body=" + body(transition));

        base.addMainActionInEmptyEnterpriseGroup(-1, transition);
        System.out.println("978 addMainActionInEmptyEnterpriseGroup(transition) -> size()=" + base.size() + " actions=" + acts(base));
        RestCallAction followUp = (RestCallAction) source.copy();
        System.out.println("980 followUp = source.copy() -> localId=" + followUp.getLocalId() + " same object? " + (followUp == source) + " auth same object? " + (followUp.getAuth() == source.getAuth()));
        followUp.resetLocalIdRecursively();
        followUp.forceNewTaints();
        System.out.println("981-982 reset + forceNewTaints -> localId=" + followUp.getLocalId());
        List<Param> pathParams = source.getParameters().stream().filter(p -> p instanceof PathParam).collect(Collectors.toList());
        String before = followUp.resolvedPath();
        followUp.bindBasedOn(source.getPath(), pathParams, null);
        System.out.println("983 bindBasedOn(source.path, pathParams, null) -> resolvedPath " + before + " -> " + followUp.resolvedPath() + " (source " + source.resolvedPath() + ")");
        base.addMainActionInEmptyEnterpriseGroup(-1, followUp);
        System.out.println("984 add followUp -> size()=" + base.size() + " actions=" + acts(base));
        base.doInitializeLocalId();
        System.out.println("986 doInitializeLocalId -> actions=" + acts(base));
        SampleType st0 = base.getSampleType();
        base.modifySampleType(SampleType.SECURITY);
        System.out.println("987 modifySampleType(SECURITY) -> " + st0 + " -> " + base.getSampleType());
        System.out.println("987 actions=" + acts(base));
        System.out.println("988 ensureFlattenedStructure() -> " + base.ensureFlattenedStructure() + " actions=" + acts(base));
        base.fixResourceForwardLinks();
        System.out.println("989 fixResourceForwardLinks -> actions=" + acts(base));
        base.verifyValidity(false);
        System.out.println("990 verifyValidity -> khong nem loi, actions=" + acts(base));
        System.out.println("victimSlice khong doi: size()=" + victimSlice.size() + " sampleType=" + victimSlice.getSampleType() + " actions=" + acts(victimSlice));

        System.out.println("##### E. ket qua gan tay 200/200/200 (log seed 2 dong 534), EvaluatedIndividual va oracle O:552-599");
        List<RestCallAction> actions = base.seeMainExecutableActions();
        List<ActionResult> results = new ArrayList<>();
        for (RestCallAction a : actions) {
            RestCallResult rr = new RestCallResult(a.getLocalId(), false);
            rr.setStatusCode(200);
            results.add(rr);
        }
        EvaluatedIndividual<RestIndividual> ei = new EvaluatedIndividual<>(new FitnessValue(3.0), base, results, null, -1,
                (org.evomaster.core.search.impact.impactinfocollection.ImpactsOfIndividual) null);
        for (RestCallAction a : actions) {
            ActionResult res = ei.seeResult(a.getLocalId());
            System.out.println("seeResult(" + a.getLocalId() + ") -> " + res.getClass().getSimpleName() + " sourceLocalId=" + res.getSourceLocalId() + " getStatusCode()=" + ((RestCallResult) res).getStatusCode()
                    + " getBody()=" + ((RestCallResult) res).getBody());
        }
        System.out.println("seeResult(\"ACTION_COMPONENT_99\") -> " + ei.seeResult("ACTION_COMPONENT_99"));
        for (EvaluatedAction ea : ei.evaluatedMainActions()) {
            System.out.println("evaluatedMainActions: action=" + ea.getAction().getName() + " result=" + ((RestCallResult) ea.getResult()).getStatusCode());
        }
        System.out.println("StatusGroup.G_2xx.isInGroup(200)=" + StatusGroup.G_2xx.isInGroup(200) + " (403)=" + StatusGroup.G_2xx.isInGroup(403) + " (null)=" + StatusGroup.G_2xx.isInGroup(null));
        RestCallAction os = actions.get(0), ot = actions.get(1), of = actions.get(2);
        System.out.println("O:580 source.auth is NoAuth=" + (((Object) os.getAuth()) instanceof NoAuth) + " looksLike(source)=" + RestSecurityBuilder.Companion.looksLikePermissionReducingTransition(os));
        System.out.println("O:583 t.auth.isDifferentFrom(source.auth)=" + ot.getAuth().isDifferentFrom(os.getAuth()) + " looksLike(t)=" + RestSecurityBuilder.Companion.looksLikePermissionReducingTransition(ot));
        System.out.println("O:586 followUp.getName()==source.getName() " + of.getName().equals(os.getName()) + " followUp.auth.isDifferentFrom(source.auth)=" + of.getAuth().isDifferentFrom(os.getAuth()));
        IdMapper idm = new IdMapper();
        String desc = idm.getFaultDescriptiveId(ExperimentalFaultCategory.SECURITY_STATEFUL_AUTHORIZATION, of.getName());
        int id = idm.handleLocalTarget(desc);
        System.out.println("O:591 getFaultDescriptiveId -> \"" + desc + "\"");
        System.out.println("O:590 handleLocalTarget -> " + id + " ; goi lai cung chuoi -> " + idm.handleLocalTarget(desc));
        FitnessValue fv = ei.getFitness();
        System.out.println("truoc updateTarget: doesCover=" + fv.doesCover(id) + " heuristic=" + fv.getHeuristic(id));
        fv.updateTarget(id, 1.0, actions.size() - 1);
        System.out.println("O:595 updateTarget(id, 1.0, " + (actions.size() - 1) + ") -> doesCover=" + fv.doesCover(id) + " heuristic=" + fv.getHeuristic(id));
        RestCallResult fr = (RestCallResult) ei.seeResult(of.getLocalId());
        System.out.println("categories truoc addFault=" + DetectedFaultUtils.INSTANCE.getDetectedFaultCategories(ei));
        fr.addFault(new DetectedFault(ExperimentalFaultCategory.SECURITY_STATEFUL_AUTHORIZATION, of.getName(), null, null));
        System.out.println("O:596 addFault -> getFaults()=" + fr.getFaults());
        System.out.println("B:1066 getDetectedFaultCategories(ei)=" + DetectedFaultUtils.INSTANCE.getDetectedFaultCategories(ei).stream().map(c -> ((Enum<?>) c).name()).collect(Collectors.toList()));
        FaultCategory cat = ExperimentalFaultCategory.SECURITY_STATEFUL_AUTHORIZATION;
        System.out.println("category code=" + cat.getCode() + " label=" + cat.getLabel() + " testCaseLabel=" + cat.getTestCaseLabel());
        EMConfig c1 = new EMConfig();
        System.out.println("EMConfig mac dinh: useExperimentalOracles=" + c1.getUseExperimentalOracles() + " isEnabledFaultCategory(970)=" + c1.isEnabledFaultCategory(cat));
        EMConfig c2 = new EMConfig();
        c2.setUseExperimentalOracles(true);
        System.out.println("EMConfig moi, useExperimentalOracles=true -> isEnabledFaultCategory(970)=" + c2.isEnabledFaultCategory(cat));

        System.out.println("##### F. RestIndividualSelectorUtils tren solution 1 ca (ei o tren)");
        List<EvaluatedIndividual<RestIndividual>> sol = List.of(ei);
        RestIndividualSelectorUtils u = RestIndividualSelectorUtils.INSTANCE;
        System.out.println("findIndividuals(PUT, /reports/{id}, status=403) -> " + u.findIndividuals(sol, HttpVerb.PUT, srcDef.getPath(), 403, null, null, null, null).size());
        System.out.println("findIndividuals(PUT, /users/{username}/role, G_2xx, authenticatedWith=superadmin) -> " + u.findIndividuals(sol, HttpVerb.PUT, tDef.getPath(), null, StatusGroup.G_2xx, null, null, "superadmin").size());
        System.out.println("findIndividuals(PUT, /users/{username}/role, G_2xx, authenticatedWith=bob) -> " + u.findIndividuals(sol, HttpVerb.PUT, tDef.getPath(), null, StatusGroup.G_2xx, null, null, "bob").size());
        List<RestIndividual> slices = u.findAndSlice(sol, HttpVerb.PUT, srcDef.getPath(), null, StatusGroup.G_2xx, null, true, null);
        System.out.println("findAndSlice(PUT, /reports/{id}, G_2xx, authenticated=true) -> " + slices.size() + " lat; lat 0 size()=" + slices.get(0).size() + " actions=" + acts(slices.get(0)));
        System.out.println("findEvaluatedActions(G_2xx) -> " + u.findEvaluatedActions(sol, null, null, null, StatusGroup.G_2xx, null).size());

        System.out.println("##### G. gene boc tren cac target khac");
        Map<String, Action> ak = load(akSpec);
        RestCallAction patch = (RestCallAction) ((RestCallAction) ak.get("PATCH:/api/v1/users/{id}")).copy();
        patch.doInitialize(new Randomness());
        ObjectGene akBody = (ObjectGene) patch.getParameters().stream().filter(p -> p instanceof BodyParam).findFirst().get().primaryGene();
        for (Gene f : akBody.getFields()) {
            if (f instanceof OptionalGene) {
                OptionalGene o = (OptionalGene) f;
                System.out.println("ak body field " + o.getName() + ": OptionalGene isActive=" + o.isActive() + " gene=" + o.getGene().getClass().getSimpleName()
                        + (o.getGene() instanceof SelectableWrapperGene ? "[isActive=" + ((SelectableWrapperGene) o.getGene()).isActive() + "] gene=" + ((SelectableWrapperGene) o.getGene()).getGene().getClass().getSimpleName() : ""));
            }
        }
        System.out.println("ak body = " + body(patch));
        Map<String, Action> va = load(vampiSpec);
        RestCallAction vr = (RestCallAction) ((RestCallAction) va.get("PUT:/users/v1/{username}/role")).copy();
        vr.doInitialize(new Randomness());
        ChoiceGene<?> choice = first(vr.getParameters().get(0), ChoiceGene.class);
        System.out.println("vampi ChoiceGene(" + choice.getName() + ") activeGeneIndex=" + choice.getActiveGeneIndex() + " children="
                + choice.getViewOfChildren().stream().map(g -> g.getClass().getSimpleName()).collect(Collectors.toList()) + " resolvedPath=" + vr.resolvedPath());
        choice.selectActiveGene(0);
        System.out.println("selectActiveGene(0) -> activeGeneIndex=" + choice.getActiveGeneIndex() + " resolvedPath=" + vr.resolvedPath());
        choice.selectActiveGene(1);
        System.out.println("selectActiveGene(1) -> activeGeneIndex=" + choice.getActiveGeneIndex() + " resolvedPath=" + vr.resolvedPath());
        for (String[] t : new String[][]{{"reports-api", reportsSpec}, {"vampi-seeded", vampiSpec}, {"pyLoad", pyloadSpec}, {"artifact-keeper", akSpec}}) {
            Map<String, Action> cl = load(t[1]);
            int n = 0;
            String firstFound = "-";
            for (Map.Entry<String, Action> e : cl.entrySet()) {
                RestCallAction a = (RestCallAction) e.getValue();
                if (a.getVerb() == HttpVerb.GET) continue;
                for (Param p : a.getParameters()) {
                    ArrayGene<?> arr = first(p, ArrayGene.class);
                    if (arr != null) {
                        n++;
                        if (firstFound.equals("-")) {
                            firstFound = e.getKey() + " " + p.getClass().getSimpleName() + "(" + p.getName() + ") ArrayGene(" + arr.getName() + ") template=" + arr.getTemplate().getClass().getSimpleName()
                                    + " minSize=" + arr.getMinSize() + " maxSize=" + arr.getMaxSize() + " elements=" + arr.getViewOfElements().size();
                        }
                    }
                }
            }
            System.out.println("ArrayGene trong tham so op ghi cua " + t[0] + ": " + n + " | dau tien: " + firstFound);
        }
    }
}
